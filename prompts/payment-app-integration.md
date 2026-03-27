# Payment App Integration Prompt

You are the integration engineer for a **Payment App** that is being onboarded to the TrustIdLayer platform as a registered external application.

---

## TrustIdLayer Scope Reference

These are **all** scopes the platform supports. When registering your app, declare only what you actually need.

| Scope            | What it grants                                                               |
|------------------|------------------------------------------------------------------------------|
| `openid`         | Required base scope — enables the OIDC authentication flow                   |
| `profile.basic`  | Read username and full name                                                  |
| `profile.email`  | Read user email address                                                      |
| `profile.phone`  | Read user phone number                                                       |
| `kyc.read`       | Read `kyc_tier` and `trust_score` summary (returned in introspection)        |
| `kyc.full`       | Read the full KYC record — document type, document number, face-similarity   |
| `consent.read`   | Read the list of consents a user has granted to client apps                  |
| `offline_access` | Issue a long-lived refresh token for server-to-server access without re-login|

---

## KYC Tier Reference

TrustIdLayer expresses KYC level as a `kyc_tier` string in all API responses.

| `kyc_tier` | Meaning                                      |
|------------|----------------------------------------------|
| `tier_0`   | Unverified — no documents submitted          |
| `tier_1`   | Basic identity verified (document only)      |
| `tier_2`   | Full KYC — document + face-match completed   |

---

## Scopes the Payment App Must Request

Register your app with the following `allowed_scopes`:

```json
["openid", "profile.basic", "profile.phone", "kyc.read", "offline_access"]
```

| Scope            | Why the Payment App needs it                                               |
|------------------|----------------------------------------------------------------------------|
| `openid`         | Required to run the authorization-code flow and authenticate users         |
| `profile.basic`  | Display the payer's name in transaction receipts and confirmation screens  |
| `profile.phone`  | Send OTP step-up challenges to the user's verified phone number            |
| `kyc.read`       | Read `kyc_tier` and `trust_score` for per-transaction limit enforcement    |
| `offline_access` | Keep server-to-server refresh tokens alive across payment sessions         |

> Do **not** request `kyc.full` unless you have a regulatory requirement to store raw document data — `kyc.read` is sufficient for transaction enforcement.

---

## Goal

Integrate sign-in with TrustIdLayer and enforce **per-transaction controls** using the user's **live `trust_score`**, **`kyc_tier`**, and **`risk_flag`** returned by TrustIdLayer token introspection.

---

## Business Rules

- Users sign in through TrustIdLayer.
- For **every transaction request**, call `POST /api/v1/auth/introspect` before authorizing payment.
- Transaction limits must reflect the live `trust_score` and `kyc_tier` at decision time.
- If introspection fails, times out, returns `active: false`, or is missing `trust_score`/`kyc_tier` — **do not process the transaction**.
- Do **not** use hardcoded defaults or cached/stale values beyond the configured TTL.
- Higher-risk profiles (`risk_flag: true` or low `trust_score`) must trigger stricter limits, step-up verification, or outright rejection.

---

## API Reference — All Endpoints Your App Will Use

Base URL: `https://<trustidlayer-host>/api/v1`

### App Registration (one-time setup)

| Method   | Path                              | Auth Required       | Purpose                                                       |
|----------|-----------------------------------|---------------------|---------------------------------------------------------------|
| `POST`   | `/apps/`                          | Bearer (owner JWT)  | Register app — returns `client_id`, `client_secret`, `api_key` |
| `GET`    | `/apps/{app_id}`                  | Bearer (owner JWT)  | Retrieve current app configuration                            |
| `PATCH`  | `/apps/{app_id}`                  | Bearer (owner JWT)  | Update name, description, scopes, redirect URIs               |
| `POST`   | `/apps/{app_id}/rotate-secret`    | Bearer (owner JWT)  | Rotate `client_secret` — returned **once only**               |
| `POST`   | `/apps/{app_id}/rotate-api-key`   | Bearer (owner JWT)  | Rotate `api_key` — returned **once only**                     |

**Registration request:**
```json
POST /api/v1/apps/
Authorization: Bearer <owner_access_token>

{
  "name": "PaymentApp",
  "description": "Enforce transaction limits based on user trust score and KYC tier",
  "allowed_scopes": ["openid", "profile.basic", "profile.phone", "kyc.read", "offline_access"],
  "redirect_uris": ["https://payment.example.com/auth/callback"]
}
```

**Registration response — save these securely:**
```json
{
  "id": "app_uuid",
  "client_id": "payment_client_xyz789",
  "client_secret": "cs_xxxxxxxxxxxxxxxx",
  "api_key": "ak_xxxxxxxxxxxxxxxx",
  "allowed_scopes": ["openid", "profile.basic", "profile.phone", "kyc.read", "offline_access"],
  "is_active": true,
  "is_approved": false
}
```

> `is_approved: false` — a TrustIdLayer admin must approve your app via `POST /apps/{app_id}/approve` before users can authenticate through it.

---

### User Sign-In Flow

| Method | Path               | Auth Required                         | Purpose                                                     |
|--------|--------------------|---------------------------------------|-------------------------------------------------------------|
| `POST` | `/auth/authorize`  | None                                  | Authenticate user, validate scopes, issue authorization code |
| `POST` | `/auth/token`      | `client_id` + `client_secret` in body | Exchange auth code → `access_token` + `refresh_token`       |
| `POST` | `/auth/token`      | `client_id` + `client_secret` in body | Refresh access token (`grant_type: refresh_token`)          |
| `GET`  | `/auth/userinfo`   | Bearer (user access token)            | Return user claims embedded in a valid access token         |
| `POST` | `/auth/logout`     | None                                  | Revoke the refresh token and end the session                |

**Authorize request (step 1):**
```json
POST /api/v1/auth/authorize

{
  "username": "jane.smith",
  "password": "user_password",
  "client_id": "payment_client_xyz789",
  "redirect_uri": "https://payment.example.com/auth/callback",
  "scope": "openid profile.basic profile.phone kyc.read offline_access",
  "state": "random_csrf_state",
  "code_challenge": "base64url(sha256(code_verifier))",
  "code_challenge_method": "S256"
}
```

**Token exchange (step 2):**
```json
POST /api/v1/auth/token

{
  "grant_type": "authorization_code",
  "client_id": "payment_client_xyz789",
  "client_secret": "cs_xxxxxxxxxxxxxxxx",
  "code": "<authorization_code>",
  "redirect_uri": "https://payment.example.com/auth/callback",
  "code_verifier": "<pkce_verifier>"
}
```

**Token response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "rt_xxxxxxxxxxxxxxxxxxxx",
  "token_type": "Bearer",
  "expires_in": 900,
  "scope": "openid profile.basic profile.phone kyc.read offline_access"
}
```

---

### Token Introspection (call before every transaction)

| Method | Path               | Auth Required                          | Purpose                                                              |
|--------|--------------------|----------------------------------------|----------------------------------------------------------------------|
| `POST` | `/auth/introspect` | `client_id` + `client_secret` in body  | Validate token and return live `trust_score`, `kyc_tier`, `risk_flag` |

**Introspect request:**
```json
POST /api/v1/auth/introspect

{
  "token": "<user_access_token>",
  "client_id": "payment_client_xyz789",
  "client_secret": "cs_xxxxxxxxxxxxxxxx"
}
```

**Introspect response — valid token:**
```json
{
  "active": true,
  "sub": "user_uuid_abc",
  "scopes": ["openid", "profile.basic", "profile.phone", "kyc.read", "offline_access"],
  "client_id": "payment_client_xyz789",
  "kyc_tier": "tier_2",
  "trust_score": 75,
  "risk_flag": false,
  "exp": 1711500900,
  "iss": "https://trustidlayer.example.com"
}
```

**Introspect response — invalid/expired/revoked token:**
```json
{
  "active": false
}
```

> **`risk_flag: true`** is automatically set by TrustIdLayer when `trust_score < 30`. This is a hard rejection signal — do not process the transaction regardless of `kyc_tier`.

---

### Webhook Subscriptions (real-time risk and KYC change notifications)

| Method   | Path                               | Auth | Purpose                                        |
|----------|------------------------------------|------|------------------------------------------------|
| `POST`   | `/webhooks/subscribe`              | None | Subscribe your endpoint to a domain event type |
| `DELETE` | `/webhooks/subscriptions/{sub_id}` | None | Deactivate a webhook subscription              |

**Available event types:**

| Event type           | When fired                               | Useful payload fields                                |
|----------------------|------------------------------------------|------------------------------------------------------|
| `KYCApprovedEvent`   | KYC submission approved by admin         | `user_id`, `kyc_id`, `tier`, `trust_score`, `occurred_at` |
| `RiskUpdatedEvent`   | User's trust score or risk flag changes  | `user_id`, `trust_score`, `risk_flag`, `occurred_at`      |
| `ConsentRevokedEvent`| User revokes consent for your app        | `user_id`, `client_id`, `consent_id`, `occurred_at`       |

**Subscribe example:**
```json
POST /api/v1/webhooks/subscribe

{
  "client_id": "payment_client_xyz789",
  "event_type": "RiskUpdatedEvent",
  "target_url": "https://payment.example.com/webhooks/trustid"
}
```

> The response contains a `signing_secret`. Use it to verify `X-TrustLayer-Signature` on every incoming webhook delivery. It is returned **only once** — store it immediately.

---

### Session Management (optional — user-facing account pages)

| Method   | Path                    | Auth Required       | Purpose                                  |
|----------|-------------------------|---------------------|------------------------------------------|
| `GET`    | `/session/me/active`    | Bearer (user token) | List all active sessions for the user    |
| `DELETE` | `/session/{token_id}`   | Bearer (user token) | Revoke a specific session                |
| `POST`   | `/session/revoke-all`   | Bearer (user token) | Revoke all active sessions for the user  |

---

### Consent Endpoints (check active user authorizations)

| Method | Path                       | Auth    | Purpose                                          |
|--------|----------------------------|---------|--------------------------------------------------|
| `GET`  | `/consent/user/{user_id}`  | Bearer  | List all active consents the user has granted    |
| `POST` | `/consent/revoke`          | None    | Revoke consent for a specific client             |

---

## Transaction Policy Model

Map `kyc_tier` + `trust_score` + `risk_flag` to transaction controls:

| `kyc_tier` | `trust_score` | `risk_flag` | Max Single Txn | Daily Limit | Step-Up Required | Decision             |
|------------|---------------|-------------|----------------|-------------|------------------|----------------------|
| `tier_0`   | Any           | Any         | $0             | $0          | N/A              | **Reject**           |
| Any        | Any           | `true`      | $0             | $0          | N/A              | **Reject**           |
| `tier_1`   | 0–40          | false       | $0             | $0          | N/A              | **Reject**           |
| `tier_1`   | 41–70         | false       | $100           | $200        | Yes (OTP)        | Allow w/ step-up     |
| `tier_1`   | 71–100        | false       | $500           | $1,000      | No               | **Allow**            |
| `tier_2`   | 0–40          | false       | $200           | $500        | Yes (OTP)        | Allow w/ step-up     |
| `tier_2`   | 41–70         | false       | $1,000         | $3,000      | No               | **Allow**            |
| `tier_2`   | 71–100        | false       | $5,000         | $15,000     | No               | **Allow**            |

---

## Real-Time Enforcement Flow

```
User initiates transaction
        │
        ▼
  Validate user access token
  (expiry + signature check)
        │
    expired? ──→ Reject
        │
        ▼
  Call POST /api/v1/auth/introspect
        │
  error / timeout ──→ Reject (reason: introspection_unavailable)
        │
  active=false ──→ Reject (reason: token_inactive)
        │
  active=true
        │
        ▼
  Evaluate kyc_tier + trust_score + risk_flag
  against transaction policy table
        │
   ┌────┴──────────────────┐──────────────────┐
   ▼                       ▼                  ▼
Reject               Allow w/ step-up       Allow
                           │
                    Trigger OTP challenge
                    (via profile.phone)
                           │
                    OTP confirmed?
                    No ──→ Reject
                    Yes ──→
                           ▼
                    Process transaction
                    + emit audit log
```

---

## Payment API Contract Examples

**Payment authorization request (your internal API):**
```json
{
  "user_id": "user_uuid_abc",
  "amount": 800,
  "currency": "USD",
  "recipient_id": "merchant_uuid",
  "transaction_type": "purchase",
  "idempotency_key": "txn-2026-03-27-abc123",
  "user_access_token": "<user_access_token>"
}
```

**Authorization response — allowed:**
```json
{
  "decision": "allowed",
  "transaction_id": "TXN-20260327-00456",
  "amount": 800,
  "currency": "USD",
  "kyc_tier_used": "tier_2",
  "trust_score_used": 75,
  "risk_flag_used": false,
  "decision_timestamp": "2026-03-27T10:00:00Z"
}
```

**Authorization response — step-up required:**
```json
{
  "decision": "step_up_required",
  "reason": "trust_score_below_threshold",
  "step_up_method": "otp",
  "kyc_tier_used": "tier_1",
  "trust_score_used": 55,
  "transaction_ref": "TXN-REF-00456"
}
```

**Authorization response — rejected:**
```json
{
  "decision": "rejected",
  "reason": "risk_flag_active",
  "kyc_tier_used": "tier_2",
  "trust_score_used": 22,
  "risk_flag_used": true,
  "decision_timestamp": "2026-03-27T10:00:00Z"
}
```

---

## Resilience and Failure Handling

- **Fail-closed**: Any introspection failure → reject transaction, never fall through to a permissive default.
- **Timeout**: Introspection call timeout: 2 seconds (configurable per environment).
- **Retry**: Max 1 retry on transient network error; if retry fails, reject and return `reason: introspection_unavailable`.
- **Circuit breaker**: Open after 5 consecutive failures; all transactions rejected while open; probe every 30 seconds.
- **Idempotency**: Every payment request must carry an `idempotency_key`; duplicate requests must return the original decision without re-processing.

---

## Security and Compliance

- Verify `active: true`, `exp` not past, and `kyc.read` in returned `scopes` before using any introspection data.
- Store `client_secret` and `api_key` in a secrets manager — never in source code or plain environment variables.
- Rotate `client_secret` on a fixed schedule using `POST /apps/{app_id}/rotate-secret`.
- Log every transaction decision with: `user_id`, `trust_score`, `kyc_tier`, `risk_flag`, `decision`, `reason_code`, `amount`, `idempotency_key`, `timestamp`. Logs must be immutable and retained per applicable financial compliance policy.
- Monitor for anomalous trust score drops (e.g., ≥ 20 points since last transaction) as a fraud signal.

---

## Testing Checklist

**Policy engine — per tier/score combination:**
- [ ] `tier_0` any score → reject.
- [ ] `risk_flag: true` any tier → reject.
- [ ] `tier_1` score 55 within limit → allow w/ OTP step-up.
- [ ] `tier_2` score 80 within limit → allow.
- [ ] `tier_2` score 80 over single-transaction limit → reject with reason code.
- [ ] `tier_2` score 80, cumulative daily limit reached → reject.

**Introspection failure paths:**
- [ ] Introspection timeout → reject, no fallback.
- [ ] `active: false` → reject.
- [ ] Missing `trust_score` in response → reject.
- [ ] Expired user token (pre-introspection check) → reject.

**Idempotency and resilience:**
- [ ] Duplicate `idempotency_key` → return original decision, no double-processing.
- [ ] Circuit breaker opens after 5 failures → all transactions rejected while open.

**Webhooks:**
- [ ] `RiskUpdatedEvent` with `risk_flag: true` → block further transactions for that user immediately.
- [ ] `KYCApprovedEvent` with upgraded `tier` → update user's transaction limits.
- [ ] `ConsentRevokedEvent` → invalidate session and prevent further transactions.
- [ ] Webhook signature verification: invalid `X-TrustLayer-Signature` → reject delivery.

**Secret management:**
- [ ] Secret rotation: old `client_secret` rejected; new one accepted within one rotation cycle.

---

## Monitoring and Alerting Plan

- [ ] Metric: introspection call latency p50 / p95 / p99.
- [ ] Metric: introspection success / failure rate per minute.
- [ ] Metric: transaction approve / reject / step-up rate by `kyc_tier` and `trust_score` band.
- [ ] Metric: step-up completion rate.
- [ ] Alert: introspection failure rate > 1% over 5 minutes → page on-call.
- [ ] Alert: circuit breaker open event → immediate escalation.
- [ ] Alert: sudden spike in rejections (> 3× baseline) → fraud investigation trigger.
- [ ] Alert: `risk_flag: true` volume spike → security review.
- [ ] Dashboard: real-time transaction decisions broken down by `kyc_tier` and `trust_score` decile.

---

## Deployment & Go-Live Checklist

- [ ] App registered in TrustIdLayer and **approved** by admin.
- [ ] `client_id`, `client_secret`, `api_key` stored in secrets manager per environment.
- [ ] Webhook subscriptions active for `RiskUpdatedEvent`, `KYCApprovedEvent`, `ConsentRevokedEvent`.
- [ ] Webhook `signing_secret` stored securely; all deliveries verified.
- [ ] Introspection endpoint URL environment-specific (dev / staging / prod).
- [ ] Sandbox testing complete — all test cases from checklist above pass.
- [ ] Canary rollout: 5% → 25% → 100% with monitoring gates at each step.
- [ ] Runbook for circuit breaker open / introspection degradation scenarios.
