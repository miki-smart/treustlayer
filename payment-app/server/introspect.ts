import { config } from "./config";
import { demoUsers } from "./demo-users";
import { recordFailure, recordSuccess, isCircuitOpen } from "./circuit-breaker";
import type { IntrospectionResult } from "../shared/types";
import type { KycTier } from "../shared/types";

const REQUIRED_SCOPE = "kyc.read";

function buildUrl(path: string): string {
  return `${config.trustIdBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

function mockIntrospectForUser(userId: string): IntrospectionResult {
  const u = demoUsers.find((d) => d.id === userId);
  if (!u) {
    return { active: false };
  }
  const exp = Math.floor(Date.now() / 1000) + 900;
  return {
    active: true,
    sub: u.id,
    scopes: ["openid", "profile.basic", "profile.phone", REQUIRED_SCOPE, "offline_access"],
    client_id: config.clientId || "demo_client",
    kyc_tier: u.kyc_tier,
    trust_score: u.trust_score,
    risk_flag: u.risk_flag,
    exp,
    iss: "https://trustidlayer.local",
  };
}

/**
 * Demo tokens: `demo:<user_id>` — no outbound call.
 * Real tokens: POST /auth/introspect on TrustIdLayer.
 */
export async function introspectToken(
  token: string,
  userIdHint?: string
): Promise<{ ok: true; data: IntrospectionResult } | { ok: false; reason: string }> {
  if (isCircuitOpen()) {
    return { ok: false, reason: "circuit_open" };
  }

  const demoPrefix = "demo:";
  if (token.startsWith(demoPrefix)) {
    const uid = token.slice(demoPrefix.length);
    const data = mockIntrospectForUser(uid);
    recordSuccess();
    return { ok: true, data };
  }
  if (config.useMock) {
    const uid = userIdHint;
    if (!uid) {
      return { ok: false, reason: "invalid_demo_token" };
    }
    const data = mockIntrospectForUser(uid);
    recordSuccess();
    return { ok: true, data };
  }

  if (!config.trustIdBaseUrl || !config.clientId || !config.clientSecret) {
    return { ok: false, reason: "introspection_unavailable" };
  }

  const body = JSON.stringify({
    token,
    client_id: config.clientId,
    client_secret: config.clientSecret,
  });

  const url = buildUrl("/api/v1/auth/introspect");

  const attempt = async (): Promise<Response> => {
    return fetchWithTimeout(
      url,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      },
      config.introspectTimeoutMs
    );
  };

  try {
    let res = await attempt();
    if (!res.ok && res.status >= 500) {
      res = await attempt();
    }
    if (!res.ok) {
      recordFailure();
      return { ok: false, reason: "introspection_unavailable" };
    }
    const data = (await res.json()) as IntrospectionResult;
    recordSuccess();
    return { ok: true, data };
  } catch {
    try {
      const res = await attempt();
      if (!res.ok) {
        recordFailure();
        return { ok: false, reason: "introspection_unavailable" };
      }
      const data = (await res.json()) as IntrospectionResult;
      recordSuccess();
      return { ok: true, data };
    } catch {
      recordFailure();
      return { ok: false, reason: "introspection_unavailable" };
    }
  }
}

export function validateIntrospectionData(data: IntrospectionResult): {
  ok: true;
  sub: string;
  kyc_tier: KycTier;
  trust_score: number;
  risk_flag: boolean;
} | { ok: false; reason: string } {
  if (!data.active) {
    return { ok: false, reason: "token_inactive" };
  }
  if (data.trust_score === undefined || data.kyc_tier === undefined) {
    return { ok: false, reason: "missing_trust_attributes" };
  }
  const scopes = data.scopes ?? [];
  if (!scopes.includes(REQUIRED_SCOPE)) {
    return { ok: false, reason: "missing_kyc_scope" };
  }
  if (!data.sub) {
    return { ok: false, reason: "missing_sub" };
  }
  return {
    ok: true,
    sub: data.sub,
    kyc_tier: data.kyc_tier,
    trust_score: data.trust_score,
    risk_flag: Boolean(data.risk_flag),
  };
}
