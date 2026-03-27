# Unified Identity Hub — Backend

FastAPI + PostgreSQL backend for the Unified Identity Hub platform.

## Quick Start (Docker)

```bash
cp .env.example .env
docker-compose up --build
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

## Quick Start (Local Dev)

```bash
# 1. Create virtualenv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment
cp .env.example .env
# Edit .env with your local Postgres credentials

# 4. Run migrations
alembic upgrade head

# 5. Seed database with sample data
python seed.py

# 6. Start the server
uvicorn app.main:app --reload --port 8000
```

## Default Credentials (after seeding)

| Email | Password | Role |
|-------|----------|------|
| admin@fininfra.io | admin123 | admin |
| abebe@example.com | user123 | user |

## API Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| Auth | `/api/v1/auth` | JWT login, logout, refresh, profile |
| Biometric | `/api/v1/biometric` | Face/voice verification with AI simulation |
| eKYC | `/api/v1/kyc` | KYC application lifecycle |
| Digital Identity | `/api/v1/identity` | DID creation and management |
| SSO | `/api/v1/sso` | Federated SSO providers, sessions, consents |
| Cards | `/api/v1/cards` | Card issuance, transactions, rules |
| Dashboard | `/api/v1/dashboard` | Aggregated stats and time-series data |
| Audit | `/api/v1/audit` | Immutable audit log (admin only) |

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Settings via pydantic-settings
│   ├── database.py        # SQLAlchemy async engine + session
│   ├── dependencies.py    # Auth dependencies
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response models
│   ├── routers/           # FastAPI routers
│   ├── services/          # Business logic
│   └── utils/             # Security, audit helpers
├── alembic/               # Database migrations
├── seed.py                # Sample data seeder
├── requirements.txt
├── docker-compose.yml
└── Dockerfile
```
