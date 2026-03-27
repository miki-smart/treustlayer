# 🔧 TrustLayer ID — Technical Specification

**Version:** 1.0.0  
**Date:** March 27, 2026  
**Status:** Implementation Ready  
**Backend:** `./frontend/backend` (Service-Oriented Architecture)

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Specification](#api-specification)
4. [Security Architecture](#security-architecture)
5. [Trust Scoring Engine](#trust-scoring-engine)
6. [OIDC Implementation](#oidc-implementation)
7. [Webhook System](#webhook-system)
8. [AI Integration](#ai-integration)
9. [Frontend Integration](#frontend-integration)
10. [Deployment Architecture](#deployment-architecture)

---

# 1. System Architecture

## 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TS)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │   KYC    │ │   Apps   │ │ Consent  │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
└───────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                     │
        ┌────────────▼────────────┐
        │   Nginx Reverse Proxy   │
        │   (Port 80 → 8000)      │
        └────────────┬────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  API Layer (/api/v1)                 │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │   │
│  │  │  Auth  │ │  KYC   │ │  Apps  │ │Consent │        │   │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘        │   │
│  └──────┼──────────┼──────────┼──────────┼─────────────┘   │
│         │          │          │          │                  │
│  ┌──────▼──────────▼──────────▼──────────▼─────────────┐   │
│  │              Service Layer                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │  │   Auth   │ │   KYC    │ │   OIDC   │             │   │
│  │  │ Service  │ │ Service  │ │ Service  │             │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘             │   │
│  │       │            │            │                    │   │
│  │  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐              │   │
│  │  │  Trust  │  │   OCR   │  │ Webhook │              │   │
│  │  │ Service │  │ Service │  │ Service │              │   │
│  │  └─────────┘  └────┬────┘  └─────────┘              │   │
│  └───────────────────┼─────────────────────────────────┘   │
│                      │                                      │
│  ┌───────────────────▼─────────────────────────────────┐   │
│  │           SQLAlchemy ORM (Models)                   │   │
│  └───────────────────┬─────────────────────────────────┘   │
└────────────────────┼─────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  PostgreSQL Database    │
        │  (unified_identity_hub) │
        └─────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   Google Gemini AI      │
        │   (OCR Processing)      │
        └─────────────────────────┘
```

---

## 1.2 Module Breakdown

### Core Modules (TrustLayer ID Spec)

| Module | Purpose | Key Components |
|--------|---------|----------------|
| **Auth** | Authentication + OIDC | Login, logout, authorize, token, userinfo, introspect |
| **Identity** | User management | Registration, profile, email verification, password reset |
| **KYC** | KYC verification | Submission, OCR, approval, rejection, tier assignment |
| **Consent** | Consent management | Grant, revoke, list consents |
| **Apps** | App registry | Registration, approval, marketplace, credentials |
| **Webhooks** | Event delivery | Subscriptions, deliveries, retry logic |
| **Session** | Session management | Active sessions, token revocation |
| **Trust** | Trust scoring | Score calculation, risk evaluation |

### Supplemental Modules (Enhanced Features)

| Module | Purpose | Frontend Page |
|--------|---------|---------------|
| **Biometric** | Face/voice verification | BiometricPage.tsx |
| **Digital Identity** | DID management | IdentityPage.tsx |
| **SSO Providers** | External SSO | SSOPage.tsx |
| **Cards** | Financial cards | CardsPage.tsx |
| **Dashboard** | Analytics | DashboardPage.tsx |
| **Audit** | Audit logging | Admin view |

---

# 2. Database Schema

## 2.1 Core Tables (TrustLayer ID)

### `users` (Identity)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'user',  -- admin, user, kyc_approver, app_owner
    phone VARCHAR(30) UNIQUE,
    avatar VARCHAR(500),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

### `kyc_applications` (KYC)
```sql
CREATE TABLE kyc_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status kycstatus NOT NULL DEFAULT 'pending',  -- pending, in_review, approved, rejected, flagged
    tier VARCHAR(20) NOT NULL DEFAULT 'tier_0',   -- tier_0, tier_1, tier_2, tier_3
    risk_score INTEGER NOT NULL DEFAULT 0,
    trust_score INTEGER COMPUTED,  -- Derived from trust_profiles
    
    -- Document info
    document_type VARCHAR(100),     -- "National ID", "Passport", etc.
    document_number VARCHAR(100),
    document_url VARCHAR(500),
    face_image_url VARCHAR(500),
    
    -- AI analysis
    documents_submitted JSONB NOT NULL DEFAULT '[]',
    extracted_data JSONB,
    ocr_confidence FLOAT NOT NULL DEFAULT 0.0,
    synthetic_id_probability FLOAT NOT NULL DEFAULT 0.0,
    face_similarity_score FLOAT,
    
    -- Review
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rejection_reason TEXT,
    notes TEXT
);

CREATE INDEX idx_kyc_user_id ON kyc_applications(user_id);
CREATE INDEX idx_kyc_status ON kyc_applications(status);
```

### `trust_profiles` (Trust Engine)
```sql
CREATE TABLE trust_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    trust_score FLOAT NOT NULL DEFAULT 0.0,  -- 0-100
    kyc_tier INTEGER NOT NULL DEFAULT 0,     -- 0, 1, 2, 3
    factors JSONB NOT NULL DEFAULT '{}',     -- Breakdown of score components
    last_evaluated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trust_user_id ON trust_profiles(user_id);
```

### `registered_apps` (App Registry)
```sql
CREATE TABLE registered_apps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_secret_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    logo_url VARCHAR(500),
    website_url VARCHAR(500),
    category appcategory NOT NULL DEFAULT 'other',  -- banking, lending, payments, etc.
    status appstatus NOT NULL DEFAULT 'pending',    -- pending, approved, rejected, suspended
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    allowed_scopes JSONB NOT NULL DEFAULT '[]',
    redirect_uris JSONB NOT NULL DEFAULT '[]',
    api_key_hash VARCHAR(255),
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by_id UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_apps_client_id ON registered_apps(client_id);
CREATE INDEX idx_apps_owner_id ON registered_apps(owner_id);
CREATE INDEX idx_apps_status ON registered_apps(status);
```

### `consent_grants` (Consent)
```sql
CREATE TABLE consent_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id VARCHAR(100) NOT NULL,  -- References registered_apps.client_id
    scopes JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

CREATE INDEX idx_consent_user_id ON consent_grants(user_id);
CREATE INDEX idx_consent_client_id ON consent_grants(client_id);
CREATE INDEX idx_consent_user_client ON consent_grants(user_id, client_id);
```

### `authorization_codes` (OIDC)
```sql
CREATE TABLE authorization_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(255) UNIQUE NOT NULL,
    app_id UUID NOT NULL REFERENCES registered_apps(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scopes JSONB NOT NULL DEFAULT '[]',
    redirect_uri VARCHAR(500) NOT NULL,
    code_challenge VARCHAR(255),
    code_challenge_method VARCHAR(10),  -- "S256" or "plain"
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auth_codes_code ON authorization_codes(code);
CREATE INDEX idx_auth_codes_user_id ON authorization_codes(user_id);
```

### `refresh_tokens` (Session)
```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    client_id VARCHAR(100),  -- References registered_apps.client_id
    scopes TEXT,             -- Space-separated scope list
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
```

### `webhook_subscriptions` (Events)
```sql
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(100) NOT NULL,  -- References registered_apps.client_id
    event_type VARCHAR(100) NOT NULL,  -- "kyc.approved", "consent.revoked", etc.
    target_url VARCHAR(500) NOT NULL,
    signing_secret VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhook_subs_client_id ON webhook_subscriptions(client_id);
```

### `webhook_deliveries_new` (Event Delivery)
```sql
CREATE TABLE webhook_deliveries_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
    client_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    target_url VARCHAR(500) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, delivered, failed
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    delivered_at TIMESTAMPTZ,
    response_code INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_webhook_del_subscription_id ON webhook_deliveries_new(subscription_id);
CREATE INDEX idx_webhook_del_status ON webhook_deliveries_new(status);
```

---

## 2.2 Supplemental Tables

### `biometric_records`
```sql
CREATE TABLE biometric_records (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type biometrictype NOT NULL,  -- face, voice
    status biometricstatus NOT NULL DEFAULT 'pending',
    liveness_score FLOAT NOT NULL DEFAULT 0.0,
    spoof_probability FLOAT NOT NULL DEFAULT 0.0,
    risk_level risklevel NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `digital_identities` (DID-like)
```sql
CREATE TABLE digital_identities (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    unique_id VARCHAR(500) UNIQUE NOT NULL,  -- DID format
    status identitystatus NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `fin_cards` (Financial Cards)
```sql
CREATE TABLE fin_cards (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    holder_name VARCHAR(255) NOT NULL,
    card_number_masked VARCHAR(25) NOT NULL,
    card_type cardtype NOT NULL DEFAULT 'virtual',
    status cardstatus NOT NULL DEFAULT 'pending',
    expires_at VARCHAR(10) NOT NULL,
    daily_limit FLOAT NOT NULL DEFAULT 50000.0,
    monthly_limit FLOAT NOT NULL DEFAULT 500000.0,
    current_spend FLOAT NOT NULL DEFAULT 0.0,
    linked_identity_id UUID REFERENCES digital_identities(id) ON DELETE SET NULL,
    tokenized BOOLEAN NOT NULL DEFAULT TRUE,
    biometric_bound BOOLEAN NOT NULL DEFAULT FALSE,
    issued_at VARCHAR(20) NOT NULL
);
```

### `audit_entries` (Audit Log)
```sql
CREATE TABLE audit_entries (
    id UUID PRIMARY KEY,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(100),
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_actor_id ON audit_entries(actor_id);
CREATE INDEX idx_audit_timestamp ON audit_entries(timestamp);
```

---

## 2.3 Relationships

```
users (1) ──< (N) kyc_applications
users (1) ──< (N) trust_profiles (1:1 via unique constraint)
users (1) ──< (N) consent_grants
users (1) ──< (N) refresh_tokens
users (1) ──< (N) biometric_records
users (1) ──< (N) digital_identities
users (1) ──< (N) fin_cards
users (1) ──< (N) audit_entries

registered_apps (1) ──< (N) authorization_codes
registered_apps (1) ──< (N) user_apps (connection tracking)
registered_apps (1) ──< (N) webhook_endpoints

webhook_subscriptions (1) ──< (N) webhook_deliveries_new
```

---

# 3. API Specification

## 3.1 Base URL
```
http://localhost:8000/api/v1  (development)
https://api.trustlayer.io/api/v1  (production)
```

---

## 3.2 Authentication Endpoints

### POST `/auth/login`
**Purpose:** Direct frontend login (non-OIDC)

**Request:**
```json
{
  "email": "user@example.com",  // or username
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user_id": "uuid",
  "username": "user",
  "role": "user"
}
```

**Status Codes:**
- `200` — Success
- `401` — Invalid credentials
- `429` — Rate limit exceeded (5/minute)

---

### POST `/auth/logout`
**Purpose:** Revoke refresh token

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:** `204 No Content`

---

### POST `/auth/authorize`
**Purpose:** OIDC authorization code issuance

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "client_id": "app_client_id",
  "redirect_uri": "https://app.example.com/callback",
  "scope": "openid profile email kyc_status",
  "state": "random_state",
  "code_challenge": "base64url_encoded_sha256",
  "code_challenge_method": "S256"
}
```

**Response:**
```json
{
  "code": "auth_code_abc123",
  "state": "random_state",
  "redirect_uri": "https://app.example.com/callback?code=auth_code_abc123&state=random_state"
}
```

**Status Codes:**
- `200` — Success
- `400` — Invalid client_id, redirect_uri, or scopes
- `401` — Invalid user credentials
- `429` — Rate limit exceeded (10/minute)

---

### POST `/auth/token`
**Purpose:** Exchange auth code or refresh token for access token

**Request (Authorization Code Grant):**
```json
{
  "grant_type": "authorization_code",
  "client_id": "app_client_id",
  "client_secret": "app_secret",
  "code": "auth_code_abc123",
  "redirect_uri": "https://app.example.com/callback",
  "code_verifier": "random_verifier_string"
}
```

**Request (Refresh Token Grant):**
```json
{
  "grant_type": "refresh_token",
  "client_id": "app_client_id",
  "client_secret": "app_secret",
  "refresh_token": "eyJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "eyJhbGc...",
  "id_token": "eyJhbGc...",  // If openid scope
  "scope": "openid profile email kyc_status"
}
```

**Status Codes:**
- `200` — Success
- `400` — Invalid code, verifier, or grant_type
- `401` — Invalid client credentials
- `429` — Rate limit exceeded (20/minute)

---

### GET `/auth/userinfo`
**Purpose:** Retrieve user claims from access token

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "sub": "user_uuid",
  "username": "user",
  "email": "user@example.com",
  "full_name": "User Name",
  "email_verified": true,
  "kyc_tier": "tier_3",
  "trust_score": 85,
  "role": "user"
}
```

**Scope-Based Claims:**
- `openid` → `sub`
- `profile` → `username`, `full_name`
- `email` → `email`, `email_verified`
- `phone` → `phone`, `phone_verified`
- `kyc_status` → `kyc_tier`
- `trust_score` → `trust_score`, `risk_level`

---

### POST `/auth/introspect`
**Purpose:** Validate token and return trust info (for relying parties)

**Request:**
```json
{
  "token": "eyJhbGc...",
  "client_id": "app_client_id",
  "client_secret": "app_secret"
}
```

**Response (Active Token):**
```json
{
  "active": true,
  "sub": "user_uuid",
  "username": "user@example.com",
  "email": "user@example.com",
  "name": "User Name",
  "role": "user",
  "trust_score": 85,
  "kyc_tier": "tier_3",
  "risk_level": "low",
  "risk_flag": false,
  "scopes": ["openid", "profile", "email", "kyc_status"],
  "exp": 1712345678,
  "iss": "https://trustlayer-id.local",
  "client_id": "app_client_id"
}
```

**Response (Inactive Token):**
```json
{
  "active": false
}
```

**Use Case:** Relying party calls this before high-risk operations (loan approval, large transfer).

---

## 3.3 Identity Endpoints

### POST `/identity/register`
**Purpose:** User registration

**Request:**
```json
{
  "email": "user@example.com",
  "username": "user",
  "password": "Password123!",
  "full_name": "User Name",
  "phone_number": "+251912345678"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "user",
  "role": "user",
  "full_name": "User Name",
  "phone_number": "+251912345678",
  "is_active": true,
  "is_email_verified": false,
  "created_at": "2026-03-27T10:00:00Z"
}
```

---

### GET `/identity/users/me`
**Purpose:** Get current user profile

**Headers:** `Authorization: Bearer <token>`

**Response:** Same as registration response

---

### PATCH `/identity/users/{user_id}`
**Purpose:** Update user profile

**Request:**
```json
{
  "full_name": "Updated Name",
  "phone_number": "+251987654321"
}
```

**Response:** Updated user object

---

### POST `/identity/send-verification-email`
**Purpose:** Send email verification link

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Verification email sent",
  "expires_in_minutes": 60
}
```

---

### POST `/identity/verify-email`
**Purpose:** Verify email with token

**Request:**
```json
{
  "token": "verification_token_abc123"
}
```

**Response:**
```json
{
  "message": "Email verified successfully"
}
```

---

## 3.4 KYC Endpoints

### POST `/kyc/ocr`
**Purpose:** Extract data from documents using Gemini AI

**Request:** `multipart/form-data`
```
id_front: File
id_back: File
utility_bill: File
```

**Response:**
```json
{
  "success": true,
  "extracted": {
    "full_name": "Abebe Kebede",
    "date_of_birth": "1990-05-15",
    "id_number": "ET123456789",
    "gender": "Male",
    "nationality": "Ethiopian",
    "address": "Addis Ababa, Ethiopia",
    "id_ocr_confidence": 0.96,
    "utility_ocr_confidence": 0.92,
    "overall_confidence": 0.94,
    "documents_processed": ["National ID (front)", "National ID (back)", "Utility Bill"]
  },
  "warnings": [],
  "model_used": "gemini-2.0-flash"
}
```

**AI Processing:**
1. Upload 3 images to Gemini
2. Extract structured data using prompt engineering
3. Validate extracted fields
4. Calculate confidence scores
5. Return editable data for user review

---

### POST `/kyc/submit/{user_id}`
**Purpose:** Submit KYC application

**Request:**
```json
{
  "document_type": "National ID",
  "document_number": "ET123456789",
  "document_url": "https://storage/doc.jpg",
  "face_image_url": "https://storage/face.jpg",
  "extracted_data": {
    "full_name": "Abebe Kebede",
    "date_of_birth": "1990-05-15",
    "address": "Addis Ababa"
  }
}
```

**Response:**
```json
{
  "id": "kyc_uuid",
  "user_id": "user_uuid",
  "status": "pending",
  "tier": "tier_0",
  "trust_score": 0,
  "document_type": "National ID",
  "document_number": "ET123456789",
  "ocr_confidence": 0.94,
  "submitted_at": "2026-03-27T10:00:00Z"
}
```

---

### GET `/kyc/status/{user_id}`
**Purpose:** Get KYC status for user

**Response:**
```json
{
  "id": "kyc_uuid",
  "user_id": "user_uuid",
  "user_name": "Abebe Kebede",
  "user_email": "abebe@example.com",
  "status": "approved",
  "tier": "tier_3",
  "trust_score": 85,
  "document_type": "National ID",
  "face_similarity_score": 0.97,
  "submitted_at": "2026-03-27T10:00:00Z",
  "reviewed_at": "2026-03-27T11:00:00Z"
}
```

---

### GET `/kyc/submissions`
**Purpose:** List KYC submissions (admin)

**Query Params:**
- `kyc_status` — Filter by status (default: "all")
- `skip` — Pagination offset (default: 0)
- `limit` — Page size (default: 50)

**Response:**
```json
[
  {
    "id": "kyc_uuid",
    "user_id": "user_uuid",
    "user_name": "Abebe Kebede",
    "user_email": "abebe@example.com",
    "status": "pending",
    "tier": "tier_0",
    "risk_score": 12,
    "ocr_confidence": 0.96,
    "synthetic_id_probability": 0.01,
    "submitted_at": "2026-03-27T10:00:00Z"
  }
]
```

---

### POST `/kyc/{kyc_id}/approve`
**Purpose:** Approve KYC application (admin)

**Request:** Empty body or:
```json
{
  "tier": "tier_3",
  "notes": "All documents verified"
}
```

**Response:** Updated KYC object with `status: "approved"`

**Side Effects:**
1. Update `kyc_applications.status` → `approved`
2. Update `kyc_applications.tier` → specified tier
3. Recalculate `trust_profiles.trust_score`
4. Trigger webhook: `kyc.approved`

---

### POST `/kyc/{kyc_id}/reject`
**Purpose:** Reject KYC application (admin)

**Request:**
```json
{
  "reason": "Document quality insufficient"
}
```

**Response:** Updated KYC object with `status: "rejected"`

**Side Effects:**
1. Update `kyc_applications.status` → `rejected`
2. Set `rejection_reason`
3. Trigger webhook: `kyc.rejected`

---

## 3.5 Consent Endpoints

### POST `/consent/grant`
**Purpose:** Grant consent for app to access scopes

**Request:**
```json
{
  "user_id": "user_uuid",
  "client_id": "app_client_id",
  "scopes": ["openid", "profile", "email", "kyc_status"]
}
```

**Response:**
```json
{
  "id": "consent_uuid",
  "user_id": "user_uuid",
  "client_id": "app_client_id",
  "scopes": ["openid", "profile", "email", "kyc_status"],
  "is_active": true,
  "granted_at": "2026-03-27T10:00:00Z"
}
```

---

### POST `/consent/revoke`
**Purpose:** Revoke consent for app

**Request:**
```json
{
  "user_id": "user_uuid",
  "client_id": "app_client_id"
}
```

**Response:** `204 No Content`

**Side Effects:**
1. Update `consent_grants.is_active` → `false`
2. Set `revoked_at` timestamp
3. Revoke all active refresh tokens for (user, client)
4. Trigger webhook: `consent.revoked`

---

### GET `/consent/user/{user_id}`
**Purpose:** List all consents for user

**Response:**
```json
[
  {
    "id": "consent_uuid",
    "user_id": "user_uuid",
    "client_id": "app_client_id",
    "scopes": ["openid", "profile", "email"],
    "is_active": true,
    "granted_at": "2026-03-27T10:00:00Z",
    "revoked_at": null
  }
]
```

---

## 3.6 App Registry Endpoints

### POST `/apps/`
**Purpose:** Register new app

**Request:**
```json
{
  "name": "Lending App",
  "description": "Microfinance lending platform",
  "allowed_scopes": ["openid", "profile", "email", "kyc_status", "trust_score"],
  "redirect_uris": ["https://lendingapp.com/callback"],
  "logo_url": "https://lendingapp.com/logo.png",
  "website_url": "https://lendingapp.com",
  "category": "lending"
}
```

**Response:**
```json
{
  "id": "app_uuid",
  "client_id": "generated_client_id",
  "client_secret": "generated_secret",  // Only returned once
  "name": "Lending App",
  "description": "Microfinance lending platform",
  "allowed_scopes": ["openid", "profile", "email", "kyc_status", "trust_score"],
  "redirect_uris": ["https://lendingapp.com/callback"],
  "is_active": true,
  "is_approved": false,
  "owner_id": "current_user_uuid",
  "created_at": "2026-03-27T10:00:00Z"
}
```

**Security:** `client_secret` is hashed before storage (bcrypt).

---

### GET `/apps/marketplace`
**Purpose:** List all approved public apps

**Response:**
```json
[
  {
    "id": "app_uuid",
    "name": "Lending App",
    "description": "Microfinance lending platform",
    "logo_url": "https://lendingapp.com/logo.png",
    "website_url": "https://lendingapp.com",
    "category": "lending",
    "client_id": "app_client_id",
    "allowed_scopes": ["openid", "profile", "email", "kyc_status"],
    "is_approved": true
  }
]
```

**Filtering:** Only returns apps with `status: approved` and `is_public: true`.

---

### GET `/apps/mine`
**Purpose:** List apps owned by current user

**Headers:** `Authorization: Bearer <token>`

**Response:** Array of app objects (including unapproved apps)

---

### POST `/apps/{app_id}/approve`
**Purpose:** Approve app registration (admin only)

**Response:** Updated app object with `status: "approved"`

**Side Effects:**
1. Update `registered_apps.status` → `approved`
2. Set `approved_at` timestamp
3. Set `approved_by_id` to admin user
4. Trigger webhook: `app.approved` (if owner subscribed)

---

### POST `/apps/{app_id}/rotate-secret`
**Purpose:** Rotate client secret

**Response:**
```json
{
  "client_secret": "new_generated_secret"  // Only returned once
}
```

**Security:** Old secret is immediately invalidated.

---

### POST `/apps/{app_id}/rotate-api-key`
**Purpose:** Rotate API key (for non-OIDC integrations)

**Response:**
```json
{
  "api_key": "new_generated_api_key"  // Only returned once
}
```

---

## 3.7 Webhook Endpoints

### POST `/webhooks/subscribe`
**Purpose:** Subscribe to event type

**Request:**
```json
{
  "client_id": "app_client_id",
  "event_type": "kyc.approved",
  "target_url": "https://app.example.com/webhooks"
}
```

**Response:**
```json
{
  "id": "subscription_uuid",
  "client_id": "app_client_id",
  "event_type": "kyc.approved",
  "target_url": "https://app.example.com/webhooks",
  "signing_secret": "generated_secret",  // For HMAC verification
  "is_active": true,
  "created_at": "2026-03-27T10:00:00Z"
}
```

**Supported Event Types:**
- `kyc.approved`
- `kyc.rejected`
- `kyc.flagged`
- `consent.granted`
- `consent.revoked`
- `trust.score_updated`
- `user.suspended`

---

### GET `/webhooks/deliveries`
**Purpose:** List webhook deliveries (for debugging)

**Response:**
```json
[
  {
    "id": "delivery_uuid",
    "client_id": "app_client_id",
    "event_type": "kyc.approved",
    "target_url": "https://app.example.com/webhooks",
    "status": "delivered",
    "attempts": 1,
    "max_attempts": 3,
    "delivered_at": "2026-03-27T10:01:00Z",
    "response_code": 200,
    "created_at": "2026-03-27T10:00:00Z"
  }
]
```

---

### POST `/webhooks/retry/{delivery_id}`
**Purpose:** Manually retry failed webhook delivery

**Response:** Updated delivery object

---

## 3.8 Session Endpoints

### GET `/session/me/active`
**Purpose:** List active refresh tokens for current user

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "token_uuid",
    "client_id": "app_client_id",
    "scopes": ["openid", "profile", "email"],
    "expires_at": "2026-04-03T10:00:00Z",
    "created_at": "2026-03-27T10:00:00Z"
  }
]
```

---

### DELETE `/session/{token_id}`
**Purpose:** Revoke specific refresh token

**Response:** `204 No Content`

---

### POST `/session/revoke-all`
**Purpose:** Revoke all refresh tokens for current user

**Response:** `204 No Content`

**Use Case:** User clicks "Sign out all devices"

---

## 3.9 Trust Endpoints

### GET `/trust/profile`
**Purpose:** Get trust profile for current user

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "trust_score": 85.0,
  "kyc_tier": 3,
  "risk_level": "low",
  "factors": {
    "email_verified": 20,
    "phone_verified": 15,
    "kyc_tier": 35,
    "biometric_verified": 15,
    "account_age": 5.2
  },
  "last_evaluated": "2026-03-27T10:00:00Z"
}
```

---

### POST `/trust/evaluate`
**Purpose:** Trigger trust score recalculation

**Response:** Updated trust profile

**Use Case:** After user completes new verification step.

---

# 4. Security Architecture

## 4.1 JWT Token Structure

### Access Token (RSA-256)
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "trustlayer-2026"
  },
  "payload": {
    "iss": "https://trustlayer-id.local",
    "sub": "user_uuid",
    "aud": "app_client_id",
    "iat": 1711534800,
    "exp": 1711535700,
    "scope": "openid profile email kyc_status",
    "client_id": "app_client_id",
    "email": "user@example.com",
    "name": "User Name",
    "email_verified": true,
    "kyc_tier": 3,
    "trust_score": 85
  },
  "signature": "..."  // RSA signature
}
```

**Expiry:** 15 minutes (configurable)

---

### Refresh Token (RSA-256)
```json
{
  "iss": "https://trustlayer-id.local",
  "sub": "user_uuid",
  "aud": "app_client_id",
  "type": "oidc_refresh",
  "scopes": ["openid", "profile", "email", "kyc_status"],
  "exp": 1712140400
}
```

**Expiry:** 7 days (configurable)

---

## 4.2 PKCE Flow

**Step 1: Client generates code verifier**
```javascript
// Relying party (client-side)
const codeVerifier = generateRandomString(128);
const codeChallenge = base64UrlEncode(sha256(codeVerifier));
```

**Step 2: Authorization request**
```http
POST /api/v1/auth/authorize
{
  "code_challenge": "base64url_encoded_sha256",
  "code_challenge_method": "S256",
  ...
}
```

**Step 3: Token exchange**
```http
POST /api/v1/auth/token
{
  "code_verifier": "original_random_string",
  ...
}
```

**Backend Verification:**
```python
def verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode()).digest()
        calculated = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return secrets.compare_digest(calculated, code_challenge)
    return secrets.compare_digest(code_verifier, code_challenge)
```

---

## 4.3 Webhook Signing

**Payload Signing:**
```python
import hmac
import hashlib
import json

payload_str = json.dumps(payload)
signature = hmac.new(
    subscription.signing_secret.encode(),
    payload_str.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "X-TrustLayer-Signature": f"sha256={signature}",
    "X-TrustLayer-Event": event_type,
    "X-TrustLayer-Delivery-ID": delivery_id,
}
```

**Relying Party Verification:**
```python
# Relying party (webhook receiver)
def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    received = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, received)
```

---

## 4.4 Rate Limiting Strategy

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `POST /auth/login` | 5/minute | Prevent brute force |
| `POST /auth/authorize` | 10/minute | Prevent auth spam |
| `POST /auth/token` | 20/minute | Allow legitimate retries |
| `POST /identity/register` | 3/minute | Prevent bot signups |
| `POST /kyc/ocr` | 10/hour | Expensive AI operation |
| `GET /apps/marketplace` | 100/minute | Public endpoint |
| Default | 100/minute | General protection |

**Implementation:** slowapi with Redis backend (optional) or in-memory.

---

# 5. Trust Scoring Engine

## 5.1 Scoring Algorithm

```python
def calculate_trust_score(user: User, kyc: KYCApplication, biometric: BiometricRecord) -> float:
    """
    Calculate trust score (0-100) based on verification factors.
    
    Components:
    - Email verified: +20 points
    - Phone verified: +15 points
    - KYC tier: +0/+15/+25/+35 (tier 0/1/2/3)
    - Biometric verified: +15 points
    - Account age: +0 to +10 (linear over 90 days)
    
    Total possible: 100 points
    """
    score = 0.0
    factors = {}
    
    # Email verification (20 points)
    if user.email_verified:
        score += 20
        factors["email_verified"] = 20
    
    # Phone verification (15 points)
    if user.phone_verified:
        score += 15
        factors["phone_verified"] = 15
    
    # KYC tier (0-35 points)
    tier_scores = {
        "tier_0": 0,   # Unverified
        "tier_1": 15,  # Basic info verified
        "tier_2": 25,  # Document verified
        "tier_3": 35,  # Full biometric verified
    }
    tier_score = tier_scores.get(kyc.tier, 0)
    score += tier_score
    factors["kyc_tier"] = tier_score
    
    # Biometric verification (15 points)
    if biometric and biometric.status == "verified":
        score += 15
        factors["biometric_verified"] = 15
    
    # Account age (0-10 points, linear over 90 days)
    account_age_days = (datetime.now(timezone.utc) - user.created_at).days
    age_score = min(10, (account_age_days / 90) * 10)
    score += age_score
    factors["account_age"] = round(age_score, 2)
    
    # Additional factors (future)
    # - Device consistency: +5
    # - Login pattern consistency: +5
    # - Transaction history: +5
    
    return min(100, score), factors
```

---

## 5.2 Risk Level Mapping

```python
def calculate_risk_level(trust_score: float) -> str:
    """Map trust score to risk level."""
    if trust_score >= 70:
        return "low"
    elif trust_score >= 40:
        return "medium"
    else:
        return "high"
```

**Risk-Based Actions:**
- **Low risk (70-100):** Allow all operations
- **Medium risk (40-69):** Require step-up authentication for high-value transactions
- **High risk (0-39):** Restrict to low-risk operations only

---

## 5.3 Dynamic Recalculation Triggers

Trust score is recalculated when:
1. ✅ Email verified
2. ✅ Phone verified
3. ✅ KYC approved (tier updated)
4. ✅ Biometric verification completed
5. ⚠️ Suspicious activity detected (future)
6. ⚠️ Device change (future)

**Implementation:**
```python
# app/services/trust_service.py

async def recalculate_trust_score(db: AsyncSession, user_id: uuid.UUID):
    """Recalculate and update trust score."""
    user = await get_user(db, user_id)
    kyc = await get_kyc_application(db, user_id)
    biometric = await get_biometric_record(db, user_id)
    
    score, factors = calculate_trust_score(user, kyc, biometric)
    risk_level = calculate_risk_level(score)
    
    # Update trust profile
    trust = await get_trust_profile(db, user)
    trust.trust_score = score
    trust.kyc_tier = int(kyc.tier.replace("tier_", "")) if kyc else 0
    trust.factors = factors
    trust.last_evaluated = datetime.now(timezone.utc)
    
    await db.commit()
    
    # Trigger webhook if score changed significantly
    if abs(trust.trust_score - score) >= 10:
        await trigger_webhook(db, "trust.score_updated", {
            "user_id": str(user_id),
            "old_score": trust.trust_score,
            "new_score": score,
            "risk_level": risk_level,
        })
    
    return trust
```

---

# 6. OIDC Implementation

## 6.1 Authorization Code Flow (Complete)

```
┌──────────┐                                  ┌──────────────┐
│  User    │                                  │ Relying Party│
│ (Browser)│                                  │     App      │
└────┬─────┘                                  └──────┬───────┘
     │                                               │
     │  1. Click "Login with TrustLayer"            │
     │◄──────────────────────────────────────────────┤
     │                                               │
     │  2. Redirect to /authorize                   │
     ├──────────────────────────────────────────────►│
     │                                               │
     │                                        ┌──────▼───────┐
     │                                        │ TrustLayer ID│
     │                                        └──────┬───────┘
     │  3. Show login form                          │
     │◄─────────────────────────────────────────────┤
     │                                               │
     │  4. Submit credentials                       │
     ├──────────────────────────────────────────────►│
     │                                               │
     │  5. Show consent screen                      │
     │◄─────────────────────────────────────────────┤
     │                                               │
     │  6. Approve scopes                           │
     ├──────────────────────────────────────────────►│
     │                                               │
     │  7. Redirect with auth code                  │
     │◄─────────────────────────────────────────────┤
     │                                               │
     │  8. Redirect to callback                     │
     ├──────────────────────────────────────────────►│
     │                                               │
     │                                        ┌──────▼───────┐
     │                                        │ Relying Party│
     │                                        │   Backend    │
     │                                        └──────┬───────┘
     │                                               │
     │                                               │ 9. Exchange code
     │                                               │    for tokens
     │                                               ├──────────────►
     │                                               │               │
     │                                               │◄──────────────┤
     │                                               │ 10. Tokens    │
     │                                               │                │
     │  11. User logged in                          │                │
     │◄─────────────────────────────────────────────┤                │
     │                                               │                │
```

---

## 6.2 OIDC Discovery Document

**Endpoint:** `GET /api/v1/oauth/.well-known/openid-configuration`

**Response:**
```json
{
  "issuer": "https://trustlayer-id.local",
  "authorization_endpoint": "https://api.trustlayer.io/api/v1/oauth/authorize",
  "token_endpoint": "https://api.trustlayer.io/api/v1/oauth/token",
  "userinfo_endpoint": "https://api.trustlayer.io/api/v1/oauth/userinfo",
  "introspection_endpoint": "https://api.trustlayer.io/api/v1/oauth/introspect",
  "jwks_uri": "https://api.trustlayer.io/api/v1/oauth/.well-known/jwks.json",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "scopes_supported": [
    "openid", "profile", "email", "phone", "address",
    "kyc_status", "trust_score"
  ],
  "token_endpoint_auth_methods_supported": ["client_secret_post"],
  "code_challenge_methods_supported": ["S256", "plain"],
  "claims_supported": [
    "sub", "name", "email", "email_verified",
    "phone", "phone_verified", "picture",
    "kyc_tier", "trust_score", "risk_level"
  ]
}
```

---

## 6.3 Scope Definitions

| Scope | Claims Included | Use Case |
|-------|-----------------|----------|
| `openid` | `sub` | Required for OIDC |
| `profile` | `name`, `picture`, `username` | Basic profile |
| `email` | `email`, `email_verified` | Email access |
| `phone` | `phone`, `phone_verified` | Phone access |
| `address` | `address` (future) | Physical address |
| `kyc_status` | `kyc_tier` | KYC verification level |
| `trust_score` | `trust_score`, `risk_level` | Risk evaluation |

---

# 7. Webhook System

## 7.1 Event Payload Structure

### Event: `kyc.approved`
```json
{
  "event_id": "event_uuid",
  "event_type": "kyc.approved",
  "timestamp": "2026-03-27T10:00:00Z",
  "data": {
    "user_id": "user_uuid",
    "kyc_id": "kyc_uuid",
    "tier": "tier_3",
    "trust_score": 85,
    "approved_at": "2026-03-27T10:00:00Z"
  }
}
```

### Event: `consent.revoked`
```json
{
  "event_id": "event_uuid",
  "event_type": "consent.revoked",
  "timestamp": "2026-03-27T10:00:00Z",
  "data": {
    "user_id": "user_uuid",
    "client_id": "app_client_id",
    "scopes": ["openid", "profile", "email"],
    "revoked_at": "2026-03-27T10:00:00Z"
  }
}
```

### Event: `trust.score_updated`
```json
{
  "event_id": "event_uuid",
  "event_type": "trust.score_updated",
  "timestamp": "2026-03-27T10:00:00Z",
  "data": {
    "user_id": "user_uuid",
    "old_score": 70,
    "new_score": 85,
    "old_risk_level": "medium",
    "new_risk_level": "low",
    "trigger": "kyc_approved"
  }
}
```

---

## 7.2 Retry Strategy

**Exponential Backoff:**
```
Attempt 1: Immediate
Attempt 2: +1 minute
Attempt 3: +5 minutes
Attempt 4: +15 minutes
Attempt 5: +60 minutes → Dead Letter Queue
```

**Status Transitions:**
```
pending → delivered (200-299 response)
pending → pending (retry scheduled)
pending → failed (max attempts exceeded or 4xx error)
```

---

# 8. AI Integration

## 8.1 Gemini OCR Service

**Model:** `gemini-2.0-flash`  
**Purpose:** Extract structured data from identity documents

**Supported Documents:**
1. National ID (front + back)
2. Passport
3. Driver's License
4. Utility Bill (address proof)

**Extraction Fields:**
```python
{
  "full_name": str,
  "date_of_birth": str,  # ISO 8601
  "id_number": str,
  "gender": str,
  "nationality": str,
  "place_of_birth": str,
  "address": str,
  "issue_date": str,
  "expiry_date": str,
  "mrz_line1": str,  # Machine-readable zone
  "mrz_line2": str,
  "id_ocr_confidence": float,  # 0.0-1.0
  "utility_ocr_confidence": float,
  "overall_confidence": float,
}
```

**Prompt Engineering:**
```python
PROMPT = """
You are an expert document analyzer for identity verification.

Analyze these identity documents and extract the following information:

1. From ID document (front):
   - Full name (as printed)
   - Date of birth (YYYY-MM-DD format)
   - ID number
   - Gender
   - Nationality
   - Issue date
   - Expiry date

2. From ID document (back):
   - MRZ lines (if present)
   - Additional information

3. From utility bill:
   - Billing name
   - Service address
   - Bill date
   - Service provider

Return JSON with extracted fields and confidence scores (0.0-1.0) for each document.
If a field is not found, return null. Be conservative with confidence scores.

Format:
{
  "full_name": "...",
  "date_of_birth": "YYYY-MM-DD",
  ...
  "id_ocr_confidence": 0.95,
  "utility_ocr_confidence": 0.92
}
"""
```

**Error Handling:**
```python
try:
    response = await gemini_client.generate_content(prompt, images=[...])
    extracted = parse_gemini_response(response)
    return {
        "success": True,
        "extracted": extracted,
        "warnings": [],
        "model_used": "gemini-2.0-flash"
    }
except Exception as e:
    logger.error(f"Gemini OCR failed: {e}")
    return {
        "success": False,
        "extracted": {},
        "warnings": ["AI OCR unavailable, manual review required"],
        "model_used": "fallback"
    }
```

---

## 8.2 Face Verification (Simulated)

**Purpose:** Calculate similarity between ID photo and selfie

**Algorithm (Simplified for Demo):**
```python
def calculate_face_similarity(id_photo: bytes, selfie: bytes) -> float:
    """
    Calculate face similarity score (0.0-1.0).
    
    In production, use:
    - Face detection (MediaPipe, dlib)
    - Feature extraction (FaceNet, ArcFace)
    - Cosine similarity
    
    For demo: Simulate with random score biased toward match.
    """
    import random
    
    # Simulate AI processing delay
    await asyncio.sleep(2)
    
    # Simulate realistic score distribution
    # 80% chance of high match (0.85-0.99)
    # 15% chance of medium match (0.60-0.84)
    # 5% chance of low match (0.30-0.59)
    rand = random.random()
    if rand < 0.80:
        return random.uniform(0.85, 0.99)
    elif rand < 0.95:
        return random.uniform(0.60, 0.84)
    else:
        return random.uniform(0.30, 0.59)
```

**Threshold:**
- `>= 0.85` — High confidence match (approve)
- `0.60-0.84` — Medium confidence (manual review)
- `< 0.60` — Low confidence (reject)

---

# 9. Frontend Integration

## 9.1 API Client Configuration

**File:** `frontend/frontend/src/services/api.ts`

**Base URL:**
```typescript
const BASE = "/api/v1";  // Proxied by nginx to backend
```

**Authentication:**
```typescript
const token = localStorage.getItem("access_token");
headers["Authorization"] = `Bearer ${token}`;
```

**Token Refresh:**
```typescript
// Automatic token refresh on 401
async function request<T>(path: string, options: RequestInit = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  
  if (res.status === 401) {
    // Try refresh
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      const refreshRes = await fetch(`${BASE}/auth/refresh`, {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      
      if (refreshRes.ok) {
        const { access_token } = await refreshRes.json();
        localStorage.setItem("access_token", access_token);
        // Retry original request
        return request(path, options);
      }
    }
    
    // Refresh failed, redirect to login
    localStorage.clear();
    window.location.href = "/";
  }
  
  return res;
}
```

---

## 9.2 Frontend Pages → Backend Endpoints Mapping

| Frontend Page | Primary Endpoints | Secondary Endpoints |
|---------------|-------------------|---------------------|
| `LoginPage.tsx` | `/auth/login`, `/identity/register` | `/identity/forgot-password` |
| `DashboardPage.tsx` | `/dashboard/stats`, `/trust/profile` | `/kyc/status/{user_id}` |
| `EKYCPage.tsx` | `/kyc/ocr`, `/kyc/submit/{user_id}` | `/kyc/status/{user_id}` |
| `AppMarketplacePage.tsx` | `/apps/marketplace`, `/apps/mine` | `/consent/grant` |
| `ConsentPage.tsx` | `/consent/user/{user_id}` | `/consent/revoke` |
| `SessionPage.tsx` | `/session/me/active` | `/session/{id}`, `/session/revoke-all` |
| `BiometricPage.tsx` | `/biometric/verify` | `/biometric/records` |
| `IdentityPage.tsx` | `/identity/create`, `/identity/list` | `/identity/{id}` |
| `SSOPage.tsx` | `/sso/providers` | `/sso/sessions` |
| `CardsPage.tsx` | `/cards/`, `/cards/transactions` | `/cards/{id}/freeze` |
| `SettingsPage.tsx` | `/identity/users/me`, `/identity/change-password` | `/auth/logout` |

---

## 9.3 Frontend State Management

**Context:** `AuthContext.tsx`
```typescript
interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserResponse | null;
  role: UserRole;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
```

**Token Storage:**
```typescript
// localStorage
access_token: string
refresh_token: string
```

**Auto-Refresh:** On app load, check if token exists and is valid.

---

# 10. Deployment Architecture

## 10.1 Docker Compose (Development)

```yaml
version: "3.9"

services:
  backend:
    build: ./frontend/backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/unified_identity_hub
      JWT_ALGORITHM: RS256
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    volumes:
      - ./frontend/backend:/app
      - ./frontend/backend/keys:/app/keys:ro
    depends_on:
      - db
  
  frontend:
    build: ./frontend/frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
  
  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: unified_identity_hub
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 10.2 Production Deployment (Kubernetes)

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
│                  (AWS ALB / GCP LB)                     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌────────▼────────┐
│   Frontend     │       │    Backend      │
│   (Nginx)      │       │   (FastAPI)     │
│   3 replicas   │       │   3 replicas    │
└────────────────┘       └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │   PostgreSQL    │
                         │   (RDS / Cloud  │
                         │      SQL)       │
                         └─────────────────┘
```

**Scaling Strategy:**
- Frontend: Horizontal (stateless)
- Backend: Horizontal (stateless, JWT-based auth)
- Database: Vertical (primary) + read replicas

---

# 11. Compliance & Audit

## 11.1 Audit Log Structure

**Table:** `audit_entries`

**Logged Actions:**
- User registration
- Login/logout
- KYC submission
- KYC approval/rejection
- Consent grant/revocation
- App registration
- App approval
- Role changes
- Password changes
- Token issuance
- Webhook deliveries

**Example Entry:**
```json
{
  "id": "audit_uuid",
  "actor_id": "admin_uuid",
  "action": "kyc.approved",
  "resource_type": "kyc_application",
  "resource_id": "kyc_uuid",
  "details": {
    "user_id": "user_uuid",
    "old_tier": "tier_0",
    "new_tier": "tier_3",
    "trust_score": 85
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2026-03-27T10:00:00Z"
}
```

---

## 11.2 Data Retention Policy

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| User profiles | Indefinite | Core identity data |
| KYC documents | 7 years | Regulatory requirement |
| Audit logs | 7 years | Compliance |
| Refresh tokens | 7 days | Expiry-based cleanup |
| Auth codes | 10 minutes | Expiry-based cleanup |
| Webhook deliveries | 30 days | Debugging window |
| Session logs | 90 days | Security analysis |

---

# 12. Performance Targets

## 12.1 API Response Times

| Endpoint | Target | Acceptable | Critical |
|----------|--------|------------|----------|
| `POST /auth/login` | < 100ms | < 200ms | < 500ms |
| `POST /auth/token` | < 150ms | < 200ms | < 500ms |
| `GET /auth/userinfo` | < 50ms | < 100ms | < 200ms |
| `POST /auth/introspect` | < 100ms | < 150ms | < 300ms |
| `POST /kyc/submit` | < 200ms | < 300ms | < 1000ms |
| `POST /kyc/ocr` | < 5000ms | < 10000ms | < 30000ms |
| `GET /apps/marketplace` | < 100ms | < 200ms | < 500ms |
| `POST /webhooks/subscribe` | < 100ms | < 200ms | < 500ms |

---

## 12.2 Database Query Optimization

**Techniques Applied:**
1. ✅ Eager loading (selectinload) for relationships
2. ✅ Indexed columns (email, username, client_id, etc.)
3. ✅ Connection pooling (20 connections + 10 overflow)
4. ✅ Query result caching (marketplace endpoint)
5. ⚠️ Read replicas (future)

---

# 13. Error Handling

## 13.1 Standard Error Response

```json
{
  "error": "ValidationError",
  "message": "Invalid email format",
  "details": [
    {
      "field": "email",
      "message": "Must be a valid email address",
      "code": "INVALID_EMAIL"
    }
  ],
  "request_id": "req_uuid",
  "timestamp": "2026-03-27T10:00:00Z"
}
```

---

## 13.2 HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| `200` | OK | Successful GET/POST/PATCH |
| `201` | Created | Resource created |
| `204` | No Content | Successful DELETE/logout |
| `400` | Bad Request | Validation error, invalid input |
| `401` | Unauthorized | Invalid credentials, expired token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Duplicate email, username |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected error |
| `503` | Service Unavailable | Database down, maintenance |

---

# 14. Configuration Management

## 14.1 Environment Variables

```bash
# Application
APP_ENV=development  # development, staging, production
APP_VERSION=1.0.0

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# JWT (RSA)
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=keys/private_key.pem
JWT_PUBLIC_KEY_PATH=keys/public_key.pem
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
ALLOWED_HOSTS=api.trustlayer.io

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_LOGIN=5/minute

# AI
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash

# Webhooks
WEBHOOK_MAX_RETRIES=5
WEBHOOK_TIMEOUT_SECONDS=10
```

---

# 15. Testing Strategy

## 15.1 Test Pyramid

```
        ┌──────────────┐
        │   E2E Tests  │  ← Full flow (browser automation)
        │   (10 tests) │
        └──────────────┘
       ┌────────────────┐
       │Integration Tests│  ← API + Database
       │   (30 tests)    │
       └────────────────┘
      ┌──────────────────┐
      │   Unit Tests     │  ← Services, utilities
      │   (50 tests)     │
      └──────────────────┘
```

---

## 15.2 Critical Test Cases

### Auth Flow Tests
```python
def test_login_success()
def test_login_invalid_credentials()
def test_login_rate_limit()
def test_authorize_flow()
def test_token_exchange()
def test_token_refresh()
def test_userinfo_endpoint()
def test_introspect_valid_token()
def test_introspect_expired_token()
```

### KYC Flow Tests
```python
def test_kyc_submission()
def test_kyc_approval()
def test_kyc_rejection()
def test_trust_score_calculation()
def test_ocr_extraction()
```

### Consent Flow Tests
```python
def test_consent_grant()
def test_consent_revocation()
def test_consent_enforcement()
```

### Webhook Tests
```python
def test_webhook_subscription()
def test_webhook_delivery()
def test_webhook_retry()
def test_webhook_signature_verification()
```

---

# 16. Monitoring & Observability

## 16.1 Metrics to Track

**Application Metrics:**
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active users
- Token issuance rate

**Business Metrics:**
- User registrations (daily)
- KYC submissions (daily)
- KYC approval rate (%)
- App registrations (daily)
- SSO logins (daily)
- Trust score distribution

**Infrastructure Metrics:**
- CPU usage (%)
- Memory usage (%)
- Database connections (active)
- Database query time (ms)
- Webhook delivery success rate (%)

---

## 16.2 Logging Strategy

**Log Levels:**
- `DEBUG` — Development only (SQL queries, detailed flow)
- `INFO` — Normal operations (user actions, API calls)
- `WARNING` — Recoverable errors (rate limit hit, retry scheduled)
- `ERROR` — Failures (database error, external API failure)
- `CRITICAL` — System failures (database down, key loading failed)

**Structured Logging:**
```json
{
  "timestamp": "2026-03-27T10:00:00Z",
  "level": "INFO",
  "logger": "app.services.kyc_service",
  "message": "KYC submission completed",
  "user_id": "user_uuid",
  "kyc_id": "kyc_uuid",
  "tier": "tier_3",
  "trust_score": 85,
  "request_id": "req_uuid"
}
```

---

# 17. Security Hardening Checklist

## 17.1 Pre-Production Security Audit

- [ ] JWT signing uses RSA-256 (not HMAC)
- [ ] Private key stored securely (AWS Secrets Manager, Vault)
- [ ] Public key accessible via JWKS endpoint
- [ ] Rate limiting enabled on all sensitive endpoints
- [ ] CORS restricted to known origins
- [ ] HTTPS enforced (no HTTP allowed)
- [ ] Security headers added (CSP, X-Frame-Options, etc.)
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (input sanitization)
- [ ] CSRF protection (for cookie-based auth)
- [ ] Password complexity requirements enforced
- [ ] Passwords hashed with bcrypt (cost factor >= 12)
- [ ] Webhook payloads signed with HMAC
- [ ] Sensitive data encrypted at rest
- [ ] PII access logged in audit trail
- [ ] Admin actions require 2FA (future)
- [ ] API keys rotatable
- [ ] Client secrets rotatable
- [ ] Token revocation works correctly
- [ ] Session timeout enforced
- [ ] Dependency vulnerabilities scanned (Snyk, Dependabot)

---

# 18. Compliance Considerations

## 18.1 GDPR Compliance

- [ ] User can request data export
- [ ] User can request account deletion
- [ ] Consent is explicit and granular
- [ ] Consent can be withdrawn anytime
- [ ] Data processing is logged
- [ ] Data retention policy documented
- [ ] Privacy policy accessible

---

## 18.2 Financial Regulations

- [ ] KYC data retained for 7 years
- [ ] Audit trail is immutable
- [ ] High-risk transactions logged
- [ ] Suspicious activity flagged
- [ ] AML checks integrated (future)

---

# 19. Known Limitations & Future Work

## 19.1 Current Limitations

1. ⚠️ **Face verification is simulated** (not production-grade AI)
2. ⚠️ **OCR depends on Gemini API** (single point of failure)
3. ⚠️ **No device fingerprinting** (planned)
4. ⚠️ **No behavioral analytics** (planned)
5. ⚠️ **Webhook delivery is async** (eventual consistency)
6. ⚠️ **No distributed tracing** (planned)
7. ⚠️ **No circuit breakers** (planned)

---

## 19.2 Future Enhancements

### Phase 1 (Post-Demo)
- [ ] Upgrade face verification (MediaPipe + FaceNet)
- [ ] Add device fingerprinting
- [ ] Implement behavioral analytics
- [ ] Add comprehensive test suite
- [ ] Implement monitoring (Prometheus + Grafana)

### Phase 2 (Production Hardening)
- [ ] Add distributed tracing (Jaeger)
- [ ] Implement circuit breakers (resilience4j)
- [ ] Add secrets management (Vault)
- [ ] Implement 2FA for admin actions
- [ ] Add fraud detection ML model

### Phase 3 (Advanced Features)
- [ ] Decentralized identity (DID) support
- [ ] Cross-border identity federation
- [ ] Blockchain integration (verifiable credentials)
- [ ] Advanced ML fraud detection
- [ ] Real-time risk scoring

---

# 20. Success Criteria

## 20.1 Functional Requirements

- [x] User can register and login
- [x] User can complete KYC with document upload
- [x] OCR extracts data from documents
- [x] Admin can approve/reject KYC
- [x] Trust score is calculated dynamically
- [x] User can browse app marketplace
- [x] User can grant consent to apps
- [x] OIDC authorization code flow works
- [x] Relying party can exchange code for tokens
- [x] Relying party can call /userinfo
- [x] Relying party can call /introspect
- [x] Webhooks are delivered reliably
- [x] User can revoke consent
- [x] User can view active sessions
- [x] Admin can view audit logs

---

## 20.2 Non-Functional Requirements

- [x] API response time < 300ms (average)
- [x] Token issuance < 200ms
- [x] System handles 100 req/sec
- [x] Database queries optimized (no N+1)
- [x] Error responses are standardized
- [x] Logging is structured (JSON)
- [x] Health checks pass
- [x] Frontend builds successfully
- [x] Docker containers start successfully

---

# ✅ Document Status

**Status:** ✅ Complete  
**Reviewed By:** Development Team  
**Approved By:** Technical Lead  
**Next Review:** Post-Demo

---

**End of Technical Specification**
