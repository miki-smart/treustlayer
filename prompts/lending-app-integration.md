# Lending App Integration Prompt

You are the integration engineer for a **Lending App** that is being onboarded to the TrustIdLayer platform as a registered external application.

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
| `offline_access` | Issue a long-lived refresh token for server-to-server access without re-login |

---

## KYC Tier Reference

TrustIdLayer expresses KYC level as a `kyc_tier` string in all API responses.

| `kyc_tier` | Meaning                                      |
|------------|----------------------------------------------|
| `tier_0`   | Unverified — no documents submitted          |
| `tier_1`   | Basic identity verified (document only)      |
| `tier_2`   | Full KYC — document + face-match completed   |

---

## Scopes the Lending App Must Request

Register your app with the following `allowed_scopes`:

```json
["openid", "profile.basic", "kyc.read", "offline_access"]
```

| Scope            | Why the Lending App needs it                                              |
|------------------|---------------------------------------------------------------------------|
| `openid`         | Required to run the authorization-code flow and authenticate users        |
| `profile.basic`  | Display the borrower's name in loan agreements and decisions              |
| `kyc.read`       | Read `kyc_tier` and `trust_score` in introspection for loan eligibility   |
| `offline_access` | Keep server-to-server refresh tokens alive between loan re-evaluations    |

> Do **not** request `kyc.full` unless you have a regulatory requirement to store raw document data — `kyc.read` is sufficient for loan decisions.

---

## Goal

Integrate sign-in with TrustIdLayer and enforce lending eligibility using the user's **live `trust_score`** and **`kyc_tier`** returned by TrustIdLayer token introspection.

---

## Business Rules

- Users sign in through TrustIdLayer.
- Before approving any loan request, call `POST /api/v1/auth/introspect` to fetch the current `trust_score`, `kyc_tier`, and `risk_flag`.
- Loan eligibility and maximum lendable amount must derive solely from those fields.
- If introspection fails, times out, returns `active: false`, or is missing `trust_score` or `kyc_tier` — **reject the loan request immediately**.
- Do **not** use hardcoded defaults or cached/stale values beyond the configured TTL.

---

## API Reference — All Endpoints Your App Will Use

Base URL: `https://<trustidlayer-host>/api/v1`

### App Registration (one-time setup)

| Method   | Path                              | Auth Required       | Purpose                                                      |
|----------|-----------------------------------|---------------------|--------------------------------------------------------------|
| `POST`   | `/apps/`                          | Bearer (owner JWT)  | Register app — returns `client_id`, `client_secret`, `api_key` |
| `GET`    | `/apps/{app_id}`                  | Bearer (owner JWT)  | Retrieve current app configuration                           |
| `PATCH`  | `/apps/{app_id}`                  | Bearer (owner JWT)  | Update name, description, scopes, redirect URIs              |
| `POST`   | `/apps/{app_id}/rotate-secret`    | Bearer (owner JWT)  | Rotate `client_secret` — returned **once only**              |
| `POST`   | `/apps/{app_id}/rotate-api-key`   | Bearer (owner JWT)  | Rotate `api_key` — returned **once only**                    |

**Registration request:**
```json
POST /api/v1/apps/
Authorization: Bearer <owner_access_token>

{
  "name": "LendingApp",
  "description": "Lend cash based on user trust score and KYC tier",
  "allowed_scopes": ["openid", "profile.basic", "kyc.read", "offline_access"],
  "redirect_uris": ["https://lending.example.com/auth/callback"]
}
```

**Registration response — save these securely:**
```json
{
  "id": "app_uuid",
  "client_id": "lending_client_abc123",
  "client_secret": "cs_xxxxxxxxxxxxxxxx",
  "api_key": "ak_xxxxxxxxxxxxxxxx",
  "allowed_scopes": ["openid", "profile.basic", "kyc.read", "offline_access"],
  "is_active": true,
  "is_approved": false
}
```

> `is_approved: false` — a TrustIdLayer admin must approve your app via `POST /apps/{app_id}/approve` before users can authenticate through it.

---

### User Sign-In Flow

| Method | Path               | Auth Required                 | Purpose                                                    |
|--------|--------------------|-------------------------------|------------------------------------------------------------|
| `POST` | `/auth/authorize`  | None                          | Authenticate user, validate scopes, issue authorization code |
| `POST` | `/auth/token`      | `client_id` + `client_secret` in body | Exchange auth code → `access_token` + `refresh_token` |
| `POST` | `/auth/token`      | `client_id` + `client_secret` in body | Refresh access token (`grant_type: refresh_token`)   |
| `GET`  | `/auth/userinfo`   | Bearer (user access token)    | Return user claims embedded in a valid access token        |
| `POST` | `/auth/logout`     | None                          | Revoke the refresh token and end the session               |

**Authorize request (step 1):**
```json
POST /api/v1/auth/authorize

{
  "username": "john.doe",
  "password": "user_password",
  "client_id": "lending_client_abc123",
  "redirect_uri": "https://lending.example.com/auth/callback",
  "scope": "openid profile.basic kyc.read offline_access",
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
  "client_id": "lending_client_abc123",
  "client_secret": "cs_xxxxxxxxxxxxxxxx",
  "code": "<authorization_code>",
  "redirect_uri": "https://lending.example.com/auth/callback",
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
  "scope": "openid profile.basic kyc.read offline_access"
}
```

---

### Token Introspection (call before every loan decision)

| Method | Path               | Auth Required                          | Purpose                                                      |
|--------|--------------------|----------------------------------------|--------------------------------------------------------------|
| `POST` | `/auth/introspect` | `client_id` + `client_secret` in body  | Validate token and return live `trust_score`, `kyc_tier`, `risk_flag` |

**Introspect request:**
```json
POST /api/v1/auth/introspect

{
  "token": "<user_access_token>",
  "client_id": "lending_client_abc123",
  "client_secret": "cs_xxxxxxxxxxxxxxxx"
}
```

**Introspect response — valid token:**
```json
{
  "active": true,
  "sub": "user_uuid_abc",
  "scopes": ["openid", "profile.basic", "kyc.read", "offline_access"],
  "client_id": "lending_client_abc123",
  "kyc_tier": "tier_2",
  "trust_score": 82,
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

> **`risk_flag: true`** is automatically set by TrustIdLayer when `trust_score < 30`. Always treat this as an immediate rejection signal regardless of `kyc_tier`.

---

### Webhook Subscriptions (real-time KYC and risk change notifications)

| Method   | Path                                   | Auth    | Purpose                                          |
|----------|----------------------------------------|---------|--------------------------------------------------|
| `POST`   | `/webhooks/subscribe`                  | None    | Subscribe your endpoint to a domain event type   |
| `DELETE` | `/webhooks/subscriptions/{sub_id}`     | None    | Deactivate a webhook subscription                |

**Available event types:**

| Event type           | When fired                              | Useful payload fields                               |
|----------------------|-----------------------------------------|-----------------------------------------------------|
| `KYCApprovedEvent`   | KYC submission approved by admin        | `user_id`, `kyc_id`, `tier`, `trust_score`, `occurred_at` |
| `RiskUpdatedEvent`   | User's trust score or risk flag changes | `user_id`, `trust_score`, `risk_flag`, `occurred_at`      |
| `ConsentRevokedEvent`| User revokes consent for your app       | `user_id`, `client_id`, `consent_id`, `occurred_at`       |

**Subscribe example:**
```json
POST /api/v1/webhooks/subscribe

{
  "client_id": "lending_client_abc123",
  "event_type": "KYCApprovedEvent",
  "target_url": "https://lending.example.com/webhooks/trustid"
}
```

> The response contains a `signing_secret`. Use it to verify `X-TrustLayer-Signature` on every incoming webhook delivery. It is returned **only once** — store it immediately.

---

### Session Management (optional — user-facing account pages)

| Method   | Path                       | Auth Required       | Purpose                                 |
|----------|----------------------------|---------------------|-----------------------------------------|
| `GET`    | `/session/me/active`       | Bearer (user token) | List all active sessions for the user   |
| `DELETE` | `/session/{token_id}`      | Bearer (user token) | Revoke a specific session               |
| `POST`   | `/session/revoke-all`      | Bearer (user token) | Revoke all active sessions for the user |

---

## Lending Policy Engine

Map `kyc_tier` + `trust_score` + `risk_flag` (from introspection) to lending decisions:

| `kyc_tier` | `trust_score` | `risk_flag` | Decision        | Max Lendable | Notes                        |
|------------|---------------|-------------|-----------------|--------------|------------------------------|
| `tier_0`   | Any           | Any         | **Reject**      | $0           | KYC required before lending  |
| Any        | Any           | `true`      | **Reject**      | $0           | Auto-flagged high risk        |
| `tier_1`   | 0–40          | false       | **Reject**      | $0           | Score too low for tier_1     |
| `tier_1`   | 41–70         | false       | Manual Review   | TBD          | Analyst decision required    |
| `tier_1`   | 71–100        | false       | **Approve**     | $500         | Low-tier lending limit       |
| `tier_2`   | 0–40          | false       | Manual Review   | TBD          | High KYC but low score       |
| `tier_2`   | 41–70         | false       | **Approve**     | $2,000       | Mid-tier lending limit       |
| `tier_2`   | 71–100        | false       | **Approve**     | $10,000      | Full trust lending limit     |

---

## Lending Decision API Contract

**Loan request (your internal API):**
```json
{
  "user_id": "user_uuid_abc",
  "requested_amount": 3000,
  "currency": "USD",
  "loan_term_days": 30,
  "user_access_token": "<user_access_token>"
}
```

**Loan approval response:**
```json
{
  "decision": "approved",
  "approved_amount": 3000,
  "kyc_tier_used": "tier_2",
  "trust_score_used": 82,
  "risk_flag_used": false,
  "decision_timestamp": "2026-03-27T10:00:00Z",
  "loan_reference": "LN-20260327-00123"
}
```

**Loan rejection response:**
```json
{
  "decision": "rejected",
  "reason": "kyc_tier_insufficient",
  "kyc_tier_used": "tier_0",
  "trust_score_used": 0,
  "risk_flag_used": false,
  "decision_timestamp": "2026-03-27T10:00:00Z"
}
```

---

## Error Handling Strategy

- **Fail-closed**: Any introspection failure (network error, timeout, `active: false`, missing fields) → reject loan, return `reason: introspection_unavailable`.
- **Retry**: Max 2 retries with exponential backoff for transient network errors only.
- **Circuit breaker**: Open after 5 consecutive failures; probe every 30 seconds; reject all requests while open.
- **No stale data**: Do not reuse any prior introspection result beyond the configured TTL (recommended ≤ 60 seconds).

---

## Security Requirements

- Verify `active: true`, `exp` not past, and `kyc.read` in returned `scopes` before using any introspection data.
- Store `client_secret` and `api_key` in a secrets manager — never in source code or plain environment variables.
- Rotate `client_secret` on a fixed schedule using `POST /apps/{app_id}/rotate-secret`.
- Log every lending decision with: `user_id`, `trust_score`, `kyc_tier`, `risk_flag`, `decision`, `reason_code`, `timestamp`. Logs must be immutable and retained per your compliance policy.

---

## Testing Checklist

- [ ] Unit tests: policy engine for all `kyc_tier` × `trust_score` × `risk_flag` combinations.
- [ ] Integration test: `tier_2` + score 82 + `risk_flag: false` → approved.
- [ ] Integration test: `active: false` → rejected.
- [ ] Integration test: `risk_flag: true` at any tier → rejected.
- [ ] Negative test: introspection timeout → rejected, no fallback.
- [ ] Negative test: missing `trust_score` in response → rejected.
- [ ] Stale-TTL test: expired cache forces a fresh introspection call.
- [ ] Webhook test: `KYCApprovedEvent` delivery triggers re-evaluation of pending applications.
- [ ] Webhook test: `RiskUpdatedEvent` with new `risk_flag: true` suspends active loan offers.
- [ ] Secret rotation test: old `client_secret` rejected after rotation; new one accepted.

---

## Deployment & Observability Checklist

- [ ] App registered in TrustIdLayer and **approved** by admin.
- [ ] `client_id`, `client_secret`, `api_key` stored in secrets manager (dev / staging / prod).
- [ ] Webhook subscriptions active for `KYCApprovedEvent` and `RiskUpdatedEvent`.
- [ ] Webhook `signing_secret` stored securely; signature verified on every delivery.
- [ ] Introspection call latency metric: p50 / p95 / p99.
- [ ] Alert: introspection failure rate > 1% over 5 minutes → page on-call.
- [ ] Alert: circuit breaker open → immediate escalation.
- [ ] Alert: `risk_flag: true` spike → fraud review trigger.
- [ ] Dashboard: loan decisions by `kyc_tier` and `trust_score` decile.
- [ ] Audit logs: every loan decision + introspection evidence, retained per policy.
