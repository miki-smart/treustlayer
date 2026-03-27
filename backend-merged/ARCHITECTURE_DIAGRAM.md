# TrustLayer ID — Architecture Diagrams

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + TS)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Dashboard │ │   eKYC   │ │   Apps   │ │ Consent  │          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
└───────┼────────────┼────────────┼────────────┼────────────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                     │
        ┌────────────▼────────────┐
        │   API Gateway (/api/v1) │
        └────────────┬────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────────┐
│              TrustLayer ID Backend (Merged)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Core Infrastructure                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │  Config  │  │ Database │  │ Security │  │  Events  │  │ │
│  │  │  (RSA)   │  │ (Async)  │  │ (JWT)    │  │  (Bus)   │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              9 Domain Modules (Clean Arch)                 │ │
│  │                                                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ Identity │  │   Auth   │  │   KYC    │  │  Trust   │ │ │
│  │  │  (User)  │  │  (OIDC)  │  │ + AI OCR │  │ (Score)  │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ Consent  │  │   App    │  │ Session  │  │ Webhook  │ │ │
│  │  │ Manager  │  │ Registry │  │ Manager  │  │  System  │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │ │
│  │                                                            │ │
│  │  ┌──────────┐                                             │ │
│  │  │Dashboard │                                             │ │
│  │  │& Audit   │                                             │ │
│  │  └──────────┘                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           Infrastructure Services                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                │ │
│  │  │PostgreSQL│  │ Gemini AI│  │  Email   │                │ │
│  │  │(9 schemas)│  │   OCR    │  │  Service │                │ │
│  │  └──────────┘  └──────────┘  └──────────┘                │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌────────▼────────┐
│ Lending App    │       │ Payment App     │
│ (Relying Party)│       │ (Relying Party) │
│                │       │                 │
│ - OIDC Login   │       │ - OIDC Login    │
│ - /introspect  │       │ - /introspect   │
│ - Webhooks     │       │ - Webhooks      │
└────────────────┘       └─────────────────┘
```

---

## Clean Architecture Module Structure

```
identity/ (Example Module)
│
├── domain/                    ← Pure business logic
│   ├── entities/
│   │   └── user.py            ← Pure Python dataclass
│   ├── repositories/
│   │   └── user_repository.py ← Abstract interface
│   └── events/
│       └── user_events.py     ← Domain events
│
├── application/               ← Use cases
│   ├── use_cases/
│   │   ├── register_user.py   ← Business logic
│   │   └── email_verification.py
│   ├── services/
│   │   └── identity_service.py
│   └── dto/
│       └── user_dto.py        ← Data transfer objects
│
├── infrastructure/            ← External dependencies
│   └── persistence/
│       ├── user_model.py      ← SQLAlchemy model
│       └── user_repository_impl.py ← Concrete implementation
│
└── presentation/              ← API layer
    ├── api/
    │   └── identity_router.py ← FastAPI router
    └── schemas/
        └── user_schemas.py    ← Pydantic schemas
```

**Benefits:**
- Domain logic is framework-agnostic
- Easy to test (no database needed for domain tests)
- Easy to swap infrastructure (e.g., switch from PostgreSQL to MongoDB)
- Clear separation of concerns

---

## Database Schema Architecture

```
PostgreSQL Database: trustlayer
│
├── identity (schema)
│   └── users
│       ├── id (UUID, PK)
│       ├── email (unique)
│       ├── username (unique)
│       ├── hashed_password
│       ├── full_name
│       ├── phone_number
│       ├── avatar
│       ├── role (user/admin/kyc_approver/app_owner)
│       ├── is_active
│       ├── is_email_verified
│       ├── phone_verified
│       ├── email_verification_token_hash
│       ├── email_verification_expires_at
│       ├── password_reset_token_hash
│       ├── password_reset_expires_at
│       ├── created_at
│       └── updated_at
│
├── auth (schema)
│   └── authorization_codes
│       ├── id (UUID, PK)
│       ├── code (unique)
│       ├── client_id
│       ├── user_id (FK → identity.users)
│       ├── redirect_uri
│       ├── scopes (array)
│       ├── code_challenge (PKCE)
│       ├── code_challenge_method
│       ├── expires_at
│       ├── is_used
│       └── created_at
│
├── kyc (schema)
│   └── verifications
│       ├── id (UUID, PK)
│       ├── user_id (FK → identity.users, unique)
│       ├── status (pending/approved/rejected)
│       ├── tier (tier_0/tier_1/tier_2/tier_3)
│       ├── document_type
│       ├── document_number
│       ├── document_url
│       ├── documents_submitted (JSONB)
│       ├── extracted_data (JSONB, from Gemini OCR)
│       ├── ocr_confidence
│       ├── reviewer_id (FK → identity.users)
│       ├── rejection_reason
│       ├── notes
│       ├── verified_at
│       ├── created_at
│       └── updated_at
│
├── trust (schema)
│   └── profiles
│       ├── id (UUID, PK)
│       ├── user_id (FK → identity.users, unique)
│       ├── trust_score (0-100)
│       ├── kyc_tier (0/1/2/3)
│       ├── factors (JSONB)
│       └── last_evaluated
│
├── consent (schema)
│   └── consents
│       ├── id (UUID, PK)
│       ├── user_id (FK → identity.users)
│       ├── client_id (FK → app_registry.apps)
│       ├── scopes (array)
│       ├── is_active
│       ├── granted_at
│       └── revoked_at
│
├── app_registry (schema)
│   └── apps
│       ├── id (UUID, PK)
│       ├── client_id (unique)
│       ├── client_secret_hash
│       ├── name
│       ├── description
│       ├── logo_url
│       ├── website_url
│       ├── category (fintech/lending/payment/other)
│       ├── status (pending/approved/rejected)
│       ├── allowed_scopes (array)
│       ├── redirect_uris (array)
│       ├── owner_id (FK → identity.users)
│       ├── api_key_hash
│       ├── is_active
│       ├── is_approved
│       ├── is_public (marketplace visibility)
│       ├── approved_at
│       ├── approved_by_id (FK → identity.users)
│       └── created_at
│
├── session (schema)
│   └── refresh_tokens
│       ├── id (UUID, PK)
│       ├── token_hash (unique)
│       ├── user_id (FK → identity.users)
│       ├── client_id (FK → app_registry.apps)
│       ├── scopes (array)
│       ├── is_revoked
│       ├── expires_at
│       └── created_at
│
├── webhook (schema)
│   ├── subscriptions
│   │   ├── id (UUID, PK)
│   │   ├── client_id (FK → app_registry.apps)
│   │   ├── event_type
│   │   ├── target_url
│   │   ├── secret (for HMAC signing)
│   │   ├── is_active
│   │   └── created_at
│   │
│   └── deliveries
│       ├── id (UUID, PK)
│       ├── client_id
│       ├── event_type
│       ├── payload (JSONB)
│       ├── target_url
│       ├── status (pending/delivered/failed)
│       ├── attempts
│       ├── max_attempts
│       ├── next_retry_at
│       ├── delivered_at
│       ├── response_code
│       └── created_at
│
└── audit (schema)
    └── entries
        ├── id (UUID, PK)
        ├── actor_id (FK → identity.users)
        ├── action
        ├── resource_type
        ├── resource_id
        ├── details (JSONB)
        ├── ip_address
        ├── user_agent
        └── timestamp
```

**Total:** 9 schemas, 10 tables

---

## Event-Driven Architecture

```
User registers
    │
    ├─→ UserCreatedEvent
    │       │
    │       ├─→ Send welcome email
    │       ├─→ Create trust profile
    │       └─→ Dispatch webhook
    │
KYC approved
    │
    ├─→ KYCApprovedEvent
    │       │
    │       ├─→ Update trust score
    │       ├─→ Upgrade KYC tier
    │       └─→ Dispatch webhook
    │
Consent revoked
    │
    └─→ ConsentRevokedEvent
            │
            ├─→ Revoke refresh tokens
            └─→ Dispatch webhook
```

**Benefits:**
- Decoupled modules
- Async side effects
- Reliable event delivery
- Audit trail

---

## Security Architecture

### JWT Flow (RSA-256)

```
1. User logs in
   ↓
2. Backend signs JWT with private key
   {
     "sub": "user_id",
     "iss": "trustlayer",
     "exp": 1234567890,
     "role": "user",
     "username": "john",
     "email": "john@example.com"
   }
   ↓
3. Frontend stores JWT in localStorage
   ↓
4. Frontend sends JWT in Authorization header
   Authorization: Bearer eyJ...
   ↓
5. Backend verifies JWT with public key
   ↓
6. Backend extracts user_id and role
   ↓
7. Request proceeds
```

**Benefits:**
- Public key can be shared with relying parties
- Relying parties can verify tokens without calling backend
- More secure than HMAC (no shared secret)

---

### OIDC Authorization Flow (with PKCE)

```
Relying Party (Lending App)
    │
    │ 1. Generate code_verifier + code_challenge
    │    code_verifier = random(43-128 chars)
    │    code_challenge = SHA256(code_verifier)
    │
    ├─→ 2. Redirect to /authorize
    │      ?client_id=lending-app
    │      &redirect_uri=https://lending.com/callback
    │      &response_type=code
    │      &scope=profile.basic kyc.tier
    │      &code_challenge=abc123...
    │      &code_challenge_method=S256
    │
TrustLayer ID
    │
    ├─→ 3. User authenticates (username + password)
    │
    ├─→ 4. Check/grant consent
    │
    ├─→ 5. Generate authorization code
    │      code = random(32 bytes)
    │      store: code → {user_id, client_id, scopes, code_challenge}
    │
    ├─→ 6. Redirect back to relying party
    │      https://lending.com/callback?code=xyz789...
    │
Relying Party
    │
    ├─→ 7. Exchange code for tokens
    │      POST /token
    │      {
    │        grant_type: "authorization_code",
    │        code: "xyz789...",
    │        redirect_uri: "https://lending.com/callback",
    │        client_id: "lending-app",
    │        client_secret: "secret123",
    │        code_verifier: "original_verifier"  ← PKCE
    │      }
    │
TrustLayer ID
    │
    ├─→ 8. Verify PKCE
    │      SHA256(code_verifier) == code_challenge? ✓
    │
    ├─→ 9. Verify client credentials
    │
    ├─→ 10. Generate tokens
    │       access_token = JWT signed with private key
    │       refresh_token = random token (stored in DB)
    │
    └─→ 11. Return tokens
           {
             "access_token": "eyJ...",
             "refresh_token": "abc...",
             "token_type": "Bearer",
             "expires_in": 900,
             "scope": "profile.basic kyc.tier"
           }
```

**Security Features:**
- PKCE prevents authorization code interception
- Client secret required for token exchange
- Short-lived authorization codes (10 min)
- Short-lived access tokens (15 min)
- Long-lived refresh tokens (30 days)

---

## Trust Scoring Algorithm

```python
def calculate_trust_score(user: User, kyc: KYCVerification) -> float:
    """
    Calculate trust score (0-100) for IDaaS.
    
    Components:
    - Email verified: +25 points
    - Phone verified: +20 points
    - KYC tier: +0/+15/+30/+45 (tier 0/1/2/3)
    - Account age: +0 to +10 (over 90 days)
    
    Total: 0-100 points
    """
    score = 0.0
    factors = {}
    
    # Email verification (25 points)
    if user.is_email_verified:
        score += 25
        factors["email_verified"] = 25
    
    # Phone verification (20 points)
    if user.phone_verified:
        score += 20
        factors["phone_verified"] = 20
    
    # KYC tier (0-45 points)
    tier_scores = {
        "tier_0": 0,   # Unverified
        "tier_1": 15,  # Basic info verified
        "tier_2": 30,  # Document verified
        "tier_3": 45,  # Full KYC + address verified
    }
    tier_score = tier_scores.get(kyc.tier, 0)
    score += tier_score
    factors["kyc_tier"] = tier_score
    
    # Account age (0-10 points)
    account_age_days = (datetime.now(timezone.utc) - user.created_at).days
    age_score = min(10, (account_age_days / 90) * 10)
    score += age_score
    factors["account_age"] = round(age_score, 2)
    
    return min(100, score), factors


# Risk level mapping
def get_risk_level(trust_score: float) -> str:
    if trust_score >= 70:
        return "low"
    elif trust_score >= 40:
        return "medium"
    else:
        return "high"
```

**Example Scores:**
- New user: 0 points (high risk)
- Email verified: 25 points (high risk)
- Email + phone verified: 45 points (medium risk)
- Email + phone + tier_2 KYC: 75 points (low risk)
- Email + phone + tier_3 KYC + 90 days: 100 points (low risk)

---

## API Request Flow

```
1. Client sends request
   GET /api/v1/identity/users/me
   Authorization: Bearer eyJ...
   
2. FastAPI receives request
   
3. Dependency: get_current_user_id()
   ├─→ Extract token from header
   ├─→ Decode JWT with public key
   ├─→ Validate signature
   ├─→ Check expiration
   └─→ Return user_id
   
4. Dependency: get_async_session()
   ├─→ Create database session
   └─→ Yield session
   
5. Router handler
   ├─→ Create repository (session)
   ├─→ Create use case (repository)
   ├─→ Execute use case (user_id)
   └─→ Return response
   
6. Use case
   ├─→ Call repository.get_by_id(user_id)
   ├─→ Convert entity to DTO
   └─→ Return DTO
   
7. Repository
   ├─→ Query database
   ├─→ Convert model to entity
   └─→ Return entity
   
8. Response serialization
   ├─→ Convert DTO to Pydantic schema
   ├─→ Serialize to JSON
   └─→ Return to client
```

**Layers traversed:** Presentation → Application → Domain → Infrastructure → Database

---

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                        Presentation                         │
│                     (API Routers)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Application                            │
│                     (Use Cases)                             │
│                                                             │
│  Auth Use Case                                              │
│    ├─→ Identity Service (get user)                          │
│    ├─→ KYC Service (get tier + trust score)                 │
│    ├─→ App Registry Service (validate client)               │
│    ├─→ Consent Service (check consent)                      │
│    └─→ Session Service (create refresh token)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                        Domain                               │
│                  (Entities + Events)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Infrastructure                           │
│              (Repositories + External)                      │
└─────────────────────────────────────────────────────────────┘
```

**Cross-module communication:** Via domain events (event bus)

---

## Deployment Architecture

### Development
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────→│   Backend   │────→│  PostgreSQL │
│ localhost:  │     │ localhost:  │     │ localhost:  │
│    5173     │     │    8000     │     │    5432     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ↓
                    ┌─────────────┐
                    │  Gemini AI  │
                    │   (Cloud)   │
                    └─────────────┘
```

### Production (Docker)
```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                         │
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │   Frontend  │────→│   Backend   │────→│  PostgreSQL │  │
│  │  Container  │     │  Container  │     │  Container  │  │
│  │   :5173     │     │   :8000     │     │   :5432     │  │
│  └─────────────┘     └─────────────┘     └─────────────┘  │
│                             │                               │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ↓
                       ┌─────────────┐
                       │  Gemini AI  │
                       │   (Cloud)   │
                       └─────────────┘
```

---

## Files Created (52 files)

### Configuration (11)
- requirements.txt
- .env.example
- alembic.ini
- Dockerfile
- docker-compose.yml
- .dockerignore
- .gitignore
- pytest.ini
- README.md
- QUICKSTART.md
- MIGRATION_GUIDE.md

### Core Infrastructure (7)
- app/main.py
- app/core/config.py
- app/core/database.py
- app/core/security.py
- app/core/exceptions.py
- app/core/events.py
- app/core/event_handlers.py

### API Layer (2)
- app/api/routes.py
- app/api/dependencies.py

### Identity Module (14)
- Domain: 3 files (entities, events, repositories)
- Application: 5 files (DTOs, use cases)
- Infrastructure: 3 files (models, repository impl)
- Presentation: 3 files (router, schemas)

### Other Modules (9 stub routers)
- auth_router.py
- kyc_router.py
- trust_router.py
- consent_router.py
- app_router.py
- session_router.py
- webhook_router.py
- dashboard_router.py
- audit_router.py

### Database (3)
- app/infrastructure/db/base.py
- app/infrastructure/db/migrations/env.py
- app/infrastructure/db/migrations/versions/001_initial_idaas_schema.py

### Scripts (4)
- scripts/generate_keys.py
- scripts/generate_boilerplate.py
- scripts/generate_module_stubs.py
- scripts/README.md

### Frontend Updates (2)
- frontend/frontend/src/App.tsx
- frontend/frontend/src/components/layout/AppSidebar.tsx

### Auto-generated (85+ __init__.py files)

**Total:** 52+ manually created files + 85+ auto-generated

---

## Summary

### What You Have
1. **Three backends:**
   - Backend #1: Clean Architecture reference
   - Backend #2: Fully functional (use for demo)
   - Merged Backend: Production-grade foundation

2. **Complete documentation:**
   - Architecture design
   - Quick start guide
   - Migration guide
   - Implementation status
   - Decision matrix

3. **Updated frontend:**
   - Removed out-of-scope features
   - 6 focused pages

### What Works Right Now
- ✅ User registration
- ✅ Login/logout
- ✅ Profile management
- ✅ Email verification
- ✅ Password management
- ✅ Admin user management

### What's Stubbed
- ⚠️ OIDC flows
- ⚠️ KYC + OCR
- ⚠️ Trust scoring
- ⚠️ Consent management
- ⚠️ App marketplace
- ⚠️ Session management
- ⚠️ Webhooks
- ⚠️ Dashboard
- ⚠️ Audit

### Recommendation
**Use Backend #2 for hackathon demo.**  
**Complete merged backend for production.**

---

**Status:** Foundation complete. Ready for iterative development.
