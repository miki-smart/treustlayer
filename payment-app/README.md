# Payment app (TrustIdLayer integration)

External **payment authorization** demo: Vite + React UI and Express API that call TrustIdLayer-style **token introspection** before each transaction, enforce **KYC tier** + **trust score** + **risk** policy, **daily limits**, and **idempotency**.

## Run (from this folder)

```bash
npm install
npm run dev
```

- UI: [http://localhost:8080](http://localhost:8080) (proxies `/api` to the API)
- API: [http://localhost:3001](http://localhost:3001)

Copy `.env.example` to `.env` and set `TRUSTID_*` when pointing at a real TrustIdLayer host (`TRUSTID_USE_MOCK=false`).

## Layout

| Path | Role |
|------|------|
| `server/` | Express: `/api/v1/payments/authorize`, auth proxies, webhooks |
| `shared/` | Policy engine shared with the UI |
| `src/` | React dashboard |

See `.env.example` for configuration.
