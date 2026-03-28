import "dotenv/config";

function num(name: string, fallback: number): number {
  const v = process.env[name];
  if (v === undefined || v === "") return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export const config = {
  port: num("PORT", 3001),
  trustIdBaseUrl: (process.env.TRUSTID_BASE_URL ?? "").replace(/\/$/, ""),
  clientId: process.env.TRUSTID_CLIENT_ID ?? "",
  clientSecret: process.env.TRUSTID_CLIENT_SECRET ?? "",
  /** When true or when base URL is empty, introspection uses demo users (no outbound calls). */
  useMock: process.env.TRUSTID_USE_MOCK === "true" || !process.env.TRUSTID_BASE_URL,
  introspectTimeoutMs: num("TRUSTID_INTROSPECT_TIMEOUT_MS", 2000),
  circuitFailureThreshold: num("TRUSTID_CIRCUIT_FAILURE_THRESHOLD", 5),
  circuitOpenSeconds: num("TRUSTID_CIRCUIT_OPEN_SECONDS", 30),
  webhookSigningSecret: process.env.TRUSTID_WEBHOOK_SIGNING_SECRET ?? "",
  /** Public URL the browser uses for OAuth redirect (e.g. http://localhost:8080/auth/callback) */
  publicRedirectUri: process.env.TRUSTID_REDIRECT_URI ?? "http://localhost:8080/auth/callback",
};
