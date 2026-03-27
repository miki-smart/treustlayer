# TrustLayer ID — Quick Start Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running on localhost:5432)
- Docker (optional)

## Setup (5 minutes)

### 1. Generate RSA Keys
```powershell
cd e:\hackathon\trustIdLayer\backend-merged
py scripts/generate_keys.py
```

This will create:
- `keys/private_key.pem`
- `keys/public_key.pem`

And print the keys to console.

### 2. Create .env File
```powershell
copy .env.example .env
```

Edit `.env` and add the keys from step 1:
```env
JWT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----"

JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----"

GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Create Database
```powershell
# Using psql
psql -U postgres -c "CREATE DATABASE trustlayer;"

# Or using pgAdmin GUI
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Run Migrations
```powershell
alembic upgrade head
```

This creates 9 schemas:
- identity
- auth
- kyc
- trust
- consent
- app_registry
- session
- webhook
- audit

### 6. Start Backend
```powershell
uvicorn app.main:app --reload
```

Backend is now running on: http://localhost:8000

API docs: http://localhost:8000/docs

### 7. Start Frontend
```powershell
cd ..\frontend\frontend
npm install
npm run dev
```

Frontend is now running on: http://localhost:5173

## Test the System

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/v1/identity/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trustlayer.id",
    "username": "admin",
    "password": "password123",
    "full_name": "Admin User"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trustlayer.id",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user_id": "...",
  "username": "admin",
  "role": "user"
}
```

### 3. Get User Profile
```bash
curl -X GET http://localhost:8000/api/v1/identity/users/me \
  -H "Authorization: Bearer <access_token>"
```

## Architecture Overview

```
Frontend (React)  →  Backend (FastAPI)  →  PostgreSQL
                                       ↓
                                   Gemini AI (OCR)
```

### Backend Modules (9)
1. **Identity** — User management
2. **Auth** — OIDC/OAuth2
3. **KYC** — Verification + OCR
4. **Trust** — Scoring engine
5. **Consent** — Consent management
6. **App Registry** — OAuth2 clients
7. **Session** — Token management
8. **Webhook** — Event delivery
9. **Dashboard** — Analytics

### Frontend Pages (6)
1. **Dashboard** — Overview + trust score
2. **eKYC** — KYC submission
3. **Apps** — App marketplace
4. **Consent** — Manage consents
5. **Sessions** — Active sessions
6. **Settings** — User settings

## Next Steps

### Implement Full Modules
The current implementation has:
- ✅ Identity module (complete)
- ⚠️ Auth module (stub - needs OIDC flows)
- ⚠️ KYC module (stub - needs OCR + approval)
- ⚠️ Trust module (stub - needs scoring logic)
- ⚠️ Other modules (stubs)

### Priority Implementation Order
1. **Auth module** — OIDC flows (authorize, token, userinfo, introspect)
2. **KYC module** — Document upload + Gemini OCR + approval workflow
3. **Trust module** — Trust scoring algorithm
4. **App Registry** — OAuth2 client registration + marketplace
5. **Consent module** — Consent grant/revoke
6. **Session module** — Refresh token management
7. **Webhook module** — Event delivery with retry
8. **Dashboard module** — Analytics queries
9. **Audit module** — Audit logging

## Troubleshooting

### Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Fix:** Ensure PostgreSQL is running and DATABASE_URL in `.env` is correct.

### JWT Decode Error
```
jose.exceptions.JWTError: Invalid key
```

**Fix:** Ensure JWT_PRIVATE_KEY and JWT_PUBLIC_KEY are set correctly in `.env`.

### Import Error
```
ModuleNotFoundError: No module named 'app'
```

**Fix:** Run `pip install -r requirements.txt` and ensure you're in the `backend-merged` directory.

## Support

For issues or questions, refer to:
- `README.md` — Full documentation
- `IDAAS_ARCHITECTURE.md` — Architecture design
- `/docs` — OpenAPI documentation (when server is running)
