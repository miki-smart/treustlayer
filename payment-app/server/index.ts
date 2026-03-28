import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import express from "express";
import cors from "cors";
import { config } from "./config";

import { authorizePayment } from "./payment-service";
import { verifyTrustLayerSignature } from "./webhook-verify";
import { blockUser, unblockUser } from "./user-blocks";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();

app.use(
  cors({
    origin: [/localhost:\d+$/, /127\.0\.0\.1:\d+$/],
    credentials: true,
  })
);

const distPath = path.join(__dirname, "../dist");
const serveSpa =
  process.env.NODE_ENV === "production" && fs.existsSync(path.join(distPath, "index.html"));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "payment-app-api", mock: config.useMock });
});

app.post("/api/v1/payments/authorize", express.json(), async (req, res) => {
  try {
    const body = req.body as Record<string, unknown>;
    const parsed = {
      user_id: String(body.user_id ?? ""),
      amount: Number(body.amount),
      currency: String(body.currency ?? "USD"),
      recipient_id: String(body.recipient_id ?? ""),
      transaction_type: String(body.transaction_type ?? "purchase"),
      idempotency_key: String(body.idempotency_key ?? ""),
      user_access_token: String(body.user_access_token ?? ""),
    };
    if (!parsed.idempotency_key || !parsed.user_id || !Number.isFinite(parsed.amount)) {
      res.status(400).json({ error: "invalid_body" });
      return;
    }
    const result = await authorizePayment(parsed);
    res.json(result);
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "internal_error" });
  }
});

const DEFAULT_OIDC_SCOPES = [
  "openid",
  "profile",
  "email",
  "phone",
  "kyc_status",
  "trust_score",
];

/** Proxy: POST TrustIdLayer /api/v1/auth/authorize (no secret). */
app.post("/api/auth/authorize", express.json(), async (req, res) => {
  if (!config.trustIdBaseUrl || !config.clientId) {
    res.status(503).json({ error: "trustid_not_configured" });
    return;
  }
  try {
    const raw = req.body as Record<string, unknown>;
    const email =
      (typeof raw.email === "string" && raw.email) ||
      (typeof raw.username === "string" && raw.username) ||
      "";
    let scopes: string[] = DEFAULT_OIDC_SCOPES;
    if (Array.isArray(raw.scopes) && raw.scopes.every((s) => typeof s === "string")) {
      scopes = raw.scopes as string[];
    } else if (typeof raw.scope === "string" && raw.scope.trim()) {
      scopes = raw.scope.trim().split(/\s+/);
    }
    const body = {
      email,
      password: raw.password,
      client_id: config.clientId,
      redirect_uri: raw.redirect_uri,
      scopes,
      state: raw.state,
      code_challenge: raw.code_challenge,
      code_challenge_method: raw.code_challenge_method ?? "S256",
    };
    const r = await fetch(`${config.trustIdBaseUrl}/api/v1/auth/authorize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.status).json(data);
  } catch {
    res.status(502).json({ error: "upstream_error" });
  }
});

/** Proxy: POST TrustIdLayer /api/v1/auth/token (adds client_secret from env). */
app.post("/api/auth/token", express.json(), async (req, res) => {
  if (!config.trustIdBaseUrl || !config.clientId || !config.clientSecret) {
    res.status(503).json({ error: "trustid_not_configured" });
    return;
  }
  try {
    const body = {
      ...(req.body as object),
      client_id: config.clientId,
      client_secret: config.clientSecret,
    };
    const r = await fetch(`${config.trustIdBaseUrl}/api/v1/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.status).json(data);
  } catch {
    res.status(502).json({ error: "upstream_error" });
  }
});

app.post(
  "/api/v1/webhooks/trustid",
  express.raw({ type: "*/*", limit: "1mb" }),
  (req, res) => {
    const raw = req.body instanceof Buffer ? req.body.toString("utf8") : String(req.body ?? "");
    const sig = req.headers["x-trustlayer-signature"] as string | undefined;

    if (config.webhookSigningSecret && !verifyTrustLayerSignature(raw, sig, config.webhookSigningSecret)) {
      res.status(401).json({ error: "invalid_signature" });
      return;
    }

    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(raw) as Record<string, unknown>;
    } catch {
      res.status(400).json({ error: "invalid_json" });
      return;
    }

    const eventType = String(payload.event_type ?? payload.type ?? "");
    const userId = String(payload.user_id ?? "");

    if (eventType === "RiskUpdatedEvent" && payload.risk_flag === true && userId) {
      blockUser(userId, "risk_flag");
    }
    if (eventType === "ConsentRevokedEvent" && userId) {
      blockUser(userId, "consent_revoked");
    }
    if (eventType === "KYCApprovedEvent" && userId) {
      unblockUser(userId);
    }

    res.json({ received: true });
  }
);

if (serveSpa) {
  app.use(express.static(distPath));
  app.use((req, res, next) => {
    if (req.path.startsWith("/api")) {
      next();
      return;
    }
    res.sendFile(path.join(distPath, "index.html"), (err) => {
      if (err) next(err);
    });
  });
}

app.listen(config.port, "0.0.0.0", () => {
  console.log(`API listening on http://0.0.0.0:${config.port}`);
});
