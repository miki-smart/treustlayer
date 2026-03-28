import express from "express";
import cors from "cors";
import { config } from "./config";
import { authorizePayment } from "./payment-service";
import { verifyTrustLayerSignature } from "./webhook-verify";
import { blockUser, unblockUser } from "./user-blocks";

const app = express();

app.use(
  cors({
    origin: [/localhost:\d+$/, /127\.0\.0\.1:\d+$/],
    credentials: true,
  })
);

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

/** Proxy: POST TrustIdLayer /api/v1/auth/authorize (no secret). */
app.post("/api/auth/authorize", express.json(), async (req, res) => {
  if (!config.trustIdBaseUrl || !config.clientId) {
    res.status(503).json({ error: "trustid_not_configured" });
    return;
  }
  try {
    const body = { ...(req.body as object), client_id: config.clientId };
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

app.listen(config.port, () => {
  console.log(`API listening on http://localhost:${config.port}`);
});
