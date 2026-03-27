# 🚀 TrustLayer ID — Implementation Plan (Backend #2 Enhancement)

**Target:** Upgrade `./frontend/backend` to production-grade while maintaining frontend compatibility  
**Timeline:** 4-6 hours for critical upgrades  
**Goal:** Demo-ready system with security, performance, and feature completeness

---

## 📋 Pre-Implementation Checklist

### ✅ Current State Verification

- [x] Frontend exists at `./frontend/frontend` (React + TypeScript)
- [x] Backend exists at `./frontend/backend` (FastAPI + PostgreSQL)
- [x] Frontend API client (`api.ts`) matches backend endpoints
- [x] Database schema includes all required tables
- [x] Seed data available (`seed.py` with 30KB of test data)
- [x] Docker Compose configuration exists

### ⚠️ Known Issues to Address

- [ ] JWT signing uses HMAC-256 (should be RSA-256)
- [ ] No rate limiting (production requirement)
- [ ] CORS allows all origins (should be restricted)
- [ ] No comprehensive error handling
- [ ] Missing API documentation enhancements
- [ ] No health check with database status

---

## 🎯 Implementation Phases

---

# PHASE 1: SECURITY HARDENING (Priority: CRITICAL)

**Time Estimate:** 2-3 hours

---

## Task 1.1: Upgrade JWT to RSA-256 Signing

**Current State:**
```python
# app/config.py
SECRET_KEY: str = "insecure-dev-secret-change-in-production"
ALGORITHM: str = "HS256"
```

**Target State:**
```python
# app/config.py
JWT_ALGORITHM: str = "RS256"
JWT_PRIVATE_KEY: str = ""  # Loaded from file
JWT_PUBLIC_KEY: str = ""   # Loaded from file
```

### Implementation Steps:

**Step 1: Generate RSA Key Pair**
```bash
cd frontend/backend

# Create keys directory
mkdir -p keys

# Generate private key
openssl genrsa -out keys/private_key.pem 2048

# Extract public key
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem

# Verify keys
openssl rsa -in keys/private_key.pem -text -noout
```

**Step 2: Update Config**
```python
# app/config.py
from pathlib import Path

class Settings(BaseSettings):
    # ... existing fields ...
    
    # JWT (RSA-256)
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY_PATH: str = "keys/private_key.pem"
    JWT_PUBLIC_KEY_PATH: str = "keys/public_key.pem"
    
    @property
    def jwt_private_key(self) -> str:
        """Load private key from file."""
        path = Path(__file__).parent.parent / self.JWT_PRIVATE_KEY_PATH
        return path.read_text()
    
    @property
    def jwt_public_key(self) -> str:
        """Load public key from file."""
        path = Path(__file__).parent.parent / self.JWT_PUBLIC_KEY_PATH
        return path.read_text()
    
    # Keep SECRET_KEY for session management (non-JWT)
    SECRET_KEY: str = "insecure-dev-secret-change-in-production"
```

**Step 3: Update OIDC Service**
```python
# app/services/oidc_service.py

# Replace all jwt.encode() calls:
# OLD:
access_token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# NEW:
access_token = jwt.encode(claims, settings.jwt_private_key, algorithm=settings.JWT_ALGORITHM)

# Replace all jwt.decode() calls:
# OLD:
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

# NEW:
payload = jwt.decode(token, settings.jwt_public_key, algorithms=[settings.JWT_ALGORITHM])
```

**Step 4: Update Auth Service**
```python
# app/services/auth_service.py

# Update create_tokens() function
def create_access_token(user_id: str, role: str, extra_claims: dict = None) -> str:
    claims = {
        "sub": user_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        **(extra_claims or {}),
    }
    return jwt.encode(claims, settings.jwt_private_key, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_public_key, algorithms=[settings.JWT_ALGORITHM])
```

**Step 5: Update Dependencies**
```python
# app/dependencies.py

from jose import jwt, JWTError
from app.config import settings

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth[7:]
    try:
        # Use public key for verification
        payload = jwt.decode(
            token,
            settings.jwt_public_key,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Step 6: Update Docker Configuration**
```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - .:/app
      - ./keys:/app/keys:ro  # Mount keys as read-only
```

**Step 7: Add Public Key Endpoint**
```python
# app/routers/oidc.py

@router.get("/.well-known/jwks.json", include_in_schema=False)
async def jwks():
    """
    JSON Web Key Set — allows relying parties to verify JWT signatures.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import base64
    
    public_key_pem = settings.jwt_public_key.encode()
    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
    
    # Extract public key components (simplified — use jwcrypto in production)
    public_numbers = public_key.public_numbers()
    
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "trustlayer-2026",
                "alg": "RS256",
                "n": base64.urlsafe_b64encode(
                    public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')
                ).decode().rstrip("="),
                "e": base64.urlsafe_b64encode(
                    public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')
                ).decode().rstrip("="),
            }
        ]
    }
```

**Testing:**
```bash
# Test token generation
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fininfra.io","password":"admin123"}'

# Decode token at jwt.io (should show RS256)
```

---

## Task 1.2: Implement Rate Limiting

**Install Dependency:**
```bash
pip install slowapi
echo "slowapi==0.1.9" >> requirements.txt
```

**Implementation:**
```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(...)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to sensitive endpoints
from slowapi import Limiter
from app.main import limiter

@router.post("/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
async def login(request: Request, body: LoginRequest, db: DB):
    ...

@router.post("/authorize")
@limiter.limit("10/minute")
async def authorize(request: Request, body: AuthorizeRequest, db: DB):
    ...

@router.post("/token")
@limiter.limit("20/minute")
async def token(request: Request, body: TokenRequest, db: DB):
    ...
```

**Configuration:**
```python
# app/config.py
class Settings(BaseSettings):
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
```

---

## Task 1.3: Restrict CORS Origins

**Current:**
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # Good!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Update `.env`:**
```bash
# .env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://trustlayer-demo.com
```

**Validation:**
```python
# app/config.py
@property
def allowed_origins_list(self) -> List[str]:
    origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]
    # Validate no wildcards in production
    if self.APP_ENV == "production" and "*" in origins:
        raise ValueError("Wildcard CORS origins not allowed in production")
    return origins
```

---

## Task 1.4: Add Security Headers

**Implementation:**
```python
# app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Add trusted host middleware (production)
if settings.APP_ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS.split(",")
    )
```

---

# PHASE 2: FEATURE ENHANCEMENTS (Priority: HIGH)

**Time Estimate:** 2-3 hours

---

## Task 2.1: Enhance Trust Scoring Algorithm

**Current:**
```python
# app/services/trust_service.py
# Basic scoring logic exists
```

**Enhancement:**
```python
# app/services/trust_service.py

async def calculate_trust_score(db: AsyncSession, user: User) -> float:
    """
    Calculate trust score (0-100) based on multiple factors.
    
    Factors:
    - Email verified: +20
    - Phone verified: +15
    - KYC tier: +0/+15/+25/+35 (tier 0/1/2/3)
    - Biometric verified: +15
    - Account age: +0 to +10 (linear over 90 days)
    - Activity consistency: +0 to +5 (based on login patterns)
    """
    score = 0.0
    factors = {}
    
    # Email verification
    if user.email_verified:
        score += 20
        factors["email_verified"] = 20
    
    # Phone verification
    if user.phone_verified:
        score += 15
        factors["phone_verified"] = 15
    
    # KYC tier
    trust = await get_trust_profile(db, user)
    if trust:
        tier_scores = {0: 0, 1: 15, 2: 25, 3: 35}
        tier_score = tier_scores.get(trust.kyc_tier, 0)
        score += tier_score
        factors["kyc_tier"] = tier_score
    
    # Biometric verification
    bio_result = await db.execute(
        select(BiometricRecord)
        .where(BiometricRecord.user_id == user.id, BiometricRecord.status == BiometricStatus.verified)
        .limit(1)
    )
    if bio_result.scalar_one_or_none():
        score += 15
        factors["biometric_verified"] = 15
    
    # Account age (0-10 points over 90 days)
    account_age_days = (datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)).days
    age_score = min(10, (account_age_days / 90) * 10)
    score += age_score
    factors["account_age"] = round(age_score, 2)
    
    # Cap at 100
    score = min(100, score)
    
    return score, factors


async def evaluate_risk_level(trust_score: float) -> str:
    """Map trust score to risk level."""
    if trust_score >= 70:
        return "low"
    elif trust_score >= 40:
        return "medium"
    else:
        return "high"
```

---

## Task 2.2: Enhance Webhook Retry Logic

**Current:**
```python
# Basic retry exists in webhook_deliveries_new table
```

**Enhancement:**
```python
# app/services/webhook_service.py

import asyncio
import httpx
from datetime import datetime, timedelta

async def deliver_webhook(
    db: AsyncSession,
    delivery_id: uuid.UUID,
) -> bool:
    """
    Attempt webhook delivery with exponential backoff.
    
    Retry strategy:
    - Attempt 1: immediate
    - Attempt 2: +1 minute
    - Attempt 3: +5 minutes
    - Attempt 4: +15 minutes
    - Attempt 5: +60 minutes (DLQ)
    """
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        return False
    
    # Get subscription for signing secret
    sub_result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == delivery.subscription_id)
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription or not subscription.is_active:
        delivery.status = "failed"
        return False
    
    # Sign payload
    import hmac
    import hashlib
    import json
    
    payload_str = json.dumps(delivery.payload)
    signature = hmac.new(
        subscription.signing_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Attempt delivery
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                delivery.target_url,
                json=delivery.payload,
                headers={
                    "Content-Type": "application/json",
                    "X-TrustLayer-Signature": f"sha256={signature}",
                    "X-TrustLayer-Event": delivery.event_type,
                    "X-TrustLayer-Delivery-ID": str(delivery.id),
                }
            )
            
            delivery.response_code = response.status_code
            delivery.attempts += 1
            
            if 200 <= response.status_code < 300:
                delivery.status = "delivered"
                delivery.delivered_at = datetime.now(timezone.utc)
                await db.commit()
                return True
            else:
                # Retry logic
                if delivery.attempts >= delivery.max_attempts:
                    delivery.status = "failed"
                else:
                    delivery.status = "pending"
                    # Exponential backoff
                    delays = [60, 300, 900, 3600]  # 1m, 5m, 15m, 1h
                    delay = delays[min(delivery.attempts - 1, len(delays) - 1)]
                    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                
                await db.commit()
                return False
    
    except Exception as e:
        delivery.attempts += 1
        if delivery.attempts >= delivery.max_attempts:
            delivery.status = "failed"
        await db.commit()
        return False
```

**Background Worker:**
```python
# app/main.py

import asyncio

async def webhook_worker():
    """Background task to process pending webhook deliveries."""
    while True:
        try:
            async with AsyncSession() as db:
                # Find pending deliveries
                result = await db.execute(
                    select(WebhookDelivery)
                    .where(
                        WebhookDelivery.status == "pending",
                        or_(
                            WebhookDelivery.next_retry_at.is_(None),
                            WebhookDelivery.next_retry_at <= datetime.now(timezone.utc)
                        )
                    )
                    .limit(10)
                )
                deliveries = result.scalars().all()
                
                for delivery in deliveries:
                    await deliver_webhook(db, delivery.id)
        
        except Exception as e:
            logger.error(f"Webhook worker error: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start webhook worker
    worker_task = asyncio.create_task(webhook_worker())
    yield
    worker_task.cancel()
```

---

## Task 2.3: Add Input Validation Middleware

**Implementation:**
```python
# app/middleware/validation.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import re

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Sanitize and validate all incoming requests."""
    
    DANGEROUS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"eval\(",
        r"\.\.\/",  # Path traversal
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check query params
        for key, value in request.query_params.items():
            if any(re.search(pattern, value, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid input detected"}
                )
        
        return await call_next(request)

# app/main.py
from app.middleware.validation import InputValidationMiddleware
app.add_middleware(InputValidationMiddleware)
```

---

# PHASE 3: OBSERVABILITY & MONITORING (Priority: HIGH)

**Time Estimate:** 1-2 hours

---

## Task 3.1: Enhanced Health Check

**Current:**
```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Enhanced:**
```python
# app/routers/health.py

from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.dependencies import DB

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(db: DB):
    """
    Comprehensive health check.
    Returns 200 if all systems operational, 503 otherwise.
    """
    health_status = {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # JWT keys check
    try:
        _ = settings.jwt_private_key
        _ = settings.jwt_public_key
        health_status["checks"]["jwt_keys"] = "ok"
    except Exception as e:
        health_status["checks"]["jwt_keys"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "ok" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@router.get("/health/ready")
async def readiness_check(db: DB):
    """Kubernetes readiness probe."""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except:
        return JSONResponse(content={"ready": False}, status_code=503)

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}
```

---

## Task 3.2: Add Structured Logging

**Install Dependency:**
```bash
pip install python-json-logger
echo "python-json-logger==2.0.7" >> requirements.txt
```

**Implementation:**
```python
# app/utils/logging.py

import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured JSON logging."""
    logger = logging.getLogger()
    
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO if settings.APP_ENV == "production" else logging.DEBUG)

# app/main.py
from app.utils.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("TrustLayer ID starting", extra={"version": settings.APP_VERSION})
    yield
    logger.info("TrustLayer ID shutting down")
```

**Usage in Code:**
```python
# app/services/kyc_service.py
import logging
logger = logging.getLogger(__name__)

async def submit_kyc(db: AsyncSession, user_id: uuid.UUID, data: dict):
    logger.info("KYC submission started", extra={
        "user_id": str(user_id),
        "document_type": data.get("document_type")
    })
    # ... process ...
    logger.info("KYC submission completed", extra={
        "user_id": str(user_id),
        "tier": result.tier
    })
```

---

## Task 3.3: Add Request/Response Logging Middleware

**Implementation:**
```python
# app/middleware/logging.py

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info("Request started", extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        })
        
        response = await call_next(request)
        
        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info("Request completed", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        })
        
        return response

# app/main.py
from app.middleware.logging import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)
```

---

# PHASE 4: API DOCUMENTATION (Priority: MEDIUM)

**Time Estimate:** 1 hour

---

## Task 4.1: Enhance OpenAPI Metadata

**Implementation:**
```python
# app/main.py

app = FastAPI(
    title="TrustLayer ID",
    description="""
# TrustLayer ID — Financial-Grade Identity Infrastructure

## Overview
TrustLayer ID is a portable, AI-driven digital identity and federated authentication 
infrastructure designed for financial ecosystems.

## Key Features
- ✅ One-time KYC verification with AI-powered OCR
- ✅ Trust scoring (0-100) based on multiple verification factors
- ✅ OpenID Connect (OIDC) federated SSO
- ✅ Consent-driven identity sharing
- ✅ Real-time risk evaluation
- ✅ Webhook event system

## Authentication
All endpoints (except `/auth/login`, `/auth/register`) require Bearer token:
```
Authorization: Bearer <access_token>
```

## OIDC Integration
Relying parties should implement standard Authorization Code Flow:
1. Redirect user to `/oauth/authorize`
2. Exchange code at `/oauth/token`
3. Fetch user claims from `/oauth/userinfo`
4. Validate tokens via `/oauth/introspect` for high-risk operations

## Security
- JWT signed with RSA-256 (asymmetric)
- PKCE support for auth code flow
- Rate limiting on sensitive endpoints
- Webhook payload signing (HMAC-SHA256)

## Trust Scoring
Trust scores (0-100) are calculated based on:
- Email verification (+20)
- Phone verification (+15)
- KYC tier (+0/+15/+25/+35)
- Biometric verification (+15)
- Account age (+0 to +10)

Risk levels:
- Low: 70-100
- Medium: 40-69
- High: 0-39
""",
    version=settings.APP_VERSION,
    contact={
        "name": "TrustLayer ID Team",
        "email": "support@trustlayer.io",
    },
    license_info={
        "name": "Proprietary",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.trustlayer.io", "description": "Production"},
    ],
)
```

---

## Task 4.2: Add Endpoint Descriptions

**Example:**
```python
# app/routers/auth.py

@router.post(
    "/authorize",
    response_model=AuthorizeResponse,
    summary="OIDC Authorization",
    description="""
    Authenticate user and issue authorization code.
    
    This is the first step in the Authorization Code Flow.
    The client must provide user credentials along with OAuth2 parameters.
    
    **Flow:**
    1. User provides credentials (username/email + password)
    2. System validates client_id and redirect_uri
    3. System checks if user has granted consent for requested scopes
    4. System issues short-lived authorization code (10 min expiry)
    5. Client exchanges code for tokens at `/token` endpoint
    
    **PKCE Support:**
    Optional but recommended. Provide `code_challenge` (base64url-encoded SHA256 hash 
    of code_verifier) and `code_challenge_method` ("S256" or "plain").
    
    **Scopes:**
    - `openid` (required)
    - `profile` (name, picture)
    - `email` (email, email_verified)
    - `phone` (phone, phone_verified)
    - `kyc_status` (kyc_tier)
    - `trust_score` (trust_score, risk_level)
    """,
    responses={
        200: {
            "description": "Authorization code issued successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": "abc123...",
                        "state": "xyz789",
                        "redirect_uri": "https://app.example.com/callback?code=abc123&state=xyz789"
                    }
                }
            }
        },
        400: {"description": "Invalid request (bad client_id, redirect_uri, or scopes)"},
        401: {"description": "Invalid user credentials"},
    },
    tags=["OIDC / Federation"]
)
async def authorize(body: AuthorizeRequest, db: DB):
    ...
```

---

# PHASE 5: ERROR HANDLING STANDARDIZATION (Priority: MEDIUM)

**Time Estimate:** 1 hour

---

## Task 5.1: Standardized Error Responses

**Implementation:**
```python
# app/schemas/errors.py

from pydantic import BaseModel
from typing import Optional, List

class ErrorDetail(BaseModel):
    """Standard error detail structure."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: str

# app/main.py

from app.schemas.errors import ErrorResponse
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardize HTTP exception responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            request_id=getattr(request.state, "request_id", None),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    logger.exception("Unhandled exception", extra={
        "request_id": getattr(request.state, "request_id", None),
        "path": request.url.path,
    })
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=getattr(request.state, "request_id", None),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump()
    )
```

---

# PHASE 6: PERFORMANCE OPTIMIZATION (Priority: LOW)

**Time Estimate:** 1-2 hours (optional)

---

## Task 6.1: Add Database Connection Pooling

**Current:**
```python
# app/database.py
engine = create_async_engine(settings.DATABASE_URL)
```

**Optimized:**
```python
# app/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,          # Max connections
    max_overflow=10,       # Extra connections under load
    pool_pre_ping=True,    # Verify connection before use
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False,            # Disable SQL logging in production
)
```

---

## Task 6.2: Add Response Caching

**Install Dependency:**
```bash
pip install fastapi-cache2[redis]
echo "fastapi-cache2[redis]==0.2.1" >> requirements.txt
```

**Implementation:**
```python
# app/main.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize cache
    FastAPICache.init(InMemoryBackend(), prefix="trustlayer-cache")
    yield

# app/routers/apps.py
from fastapi_cache.decorator import cache

@router.get("/marketplace")
@cache(expire=300)  # Cache for 5 minutes
async def marketplace(db: DB):
    """List all approved apps (cached)."""
    ...
```

---

## Task 6.3: Add Database Query Optimization

**Example:**
```python
# app/services/kyc_service.py

# Before (N+1 query problem)
async def list_submissions(db: AsyncSession, status: str = "all"):
    result = await db.execute(select(KYCApplication))
    applications = result.scalars().all()
    for app in applications:
        user = await db.execute(select(User).where(User.id == app.user_id))
        app.user = user.scalar_one()  # N+1 queries!

# After (eager loading)
from sqlalchemy.orm import selectinload

async def list_submissions(db: AsyncSession, status: str = "all"):
    query = select(KYCApplication).options(
        selectinload(KYCApplication.user),
        selectinload(KYCApplication.reviewer)
    )
    if status != "all":
        query = query.where(KYCApplication.status == KYCStatus[status])
    
    result = await db.execute(query)
    return result.scalars().all()
```

---

# PHASE 7: TESTING STRATEGY (Priority: MEDIUM)

**Time Estimate:** 2-3 hours (post-demo)

---

## Task 7.1: Critical Path Tests

**Structure:**
```
tests/
├── test_auth_flow.py       # OIDC authorization + token exchange
├── test_kyc_flow.py         # KYC submission + approval
├── test_consent_flow.py     # Consent grant + revocation
├── test_webhook_flow.py     # Webhook subscription + delivery
└── conftest.py              # Shared fixtures
```

**Example:**
```python
# tests/test_auth_flow.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_full_oidc_flow(test_db, test_user, test_app):
    """Test complete OIDC Authorization Code Flow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Authorize
        auth_response = await client.post("/api/v1/auth/authorize", json={
            "username": "test@example.com",
            "password": "password123",
            "client_id": test_app.client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "scope": "openid profile email kyc_status",
            "state": "xyz123",
        })
        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        assert "code" in auth_data
        
        # Step 2: Exchange code for tokens
        token_response = await client.post("/api/v1/auth/token", json={
            "grant_type": "authorization_code",
            "client_id": test_app.client_id,
            "client_secret": "test_secret",
            "code": auth_data["code"],
            "redirect_uri": "http://localhost:3000/callback",
        })
        assert token_response.status_code == 200
        token_data = token_response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        
        # Step 3: Get user info
        userinfo_response = await client.get(
            "/api/v1/auth/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        assert userinfo_response.status_code == 200
        userinfo = userinfo_response.json()
        assert userinfo["sub"] == str(test_user.id)
        assert "kyc_tier" in userinfo
```

---

# PHASE 8: DEPLOYMENT PREPARATION (Priority: HIGH)

**Time Estimate:** 1-2 hours

---

## Task 8.1: Environment Configuration

**Create Production `.env`:**
```bash
# .env.production
APP_ENV=production
APP_VERSION=1.0.0

DATABASE_URL=postgresql+asyncpg://trustlayer:${DB_PASSWORD}@db.trustlayer.io:5432/trustlayer_prod

JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=keys/private_key.pem
JWT_PUBLIC_KEY_PATH=keys/public_key.pem

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

ALLOWED_ORIGINS=https://trustlayer.io,https://app.trustlayer.io
ALLOWED_HOSTS=api.trustlayer.io

RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_LOGIN=5/minute

GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=gemini-2.0-flash

# Webhook
WEBHOOK_MAX_RETRIES=5
WEBHOOK_TIMEOUT_SECONDS=10
```

---

## Task 8.2: Docker Production Configuration

**Create Production Dockerfile:**
```dockerfile
# Dockerfile.prod
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trustlayer && chown -R trustlayer:trustlayer /app
USER trustlayer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"]
```

---

## Task 8.3: Kubernetes Deployment Manifests

**Create Kubernetes configs:**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trustlayer-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trustlayer-backend
  template:
    metadata:
      labels:
        app: trustlayer-backend
    spec:
      containers:
      - name: backend
        image: trustlayer/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trustlayer-secrets
              key: database-url
        - name: JWT_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: trustlayer-secrets
              key: jwt-private-key
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

# PHASE 9: FRONTEND INTEGRATION VERIFICATION (Priority: CRITICAL)

**Time Estimate:** 1 hour

---

## Task 9.1: Verify All API Endpoints

**Test Checklist:**

```typescript
// frontend/frontend/src/services/api.ts

// ✅ Auth endpoints
authApi.login("admin@fininfra.io", "admin123")
authApi.logout(refresh_token)
authApi.me()
authApi.register({...})
authApi.forgotPassword("email@example.com")
authApi.resetPassword(token, "newpass")
authApi.changePassword(user_id, "old", "new")
authApi.sendVerificationEmail()
authApi.verifyEmail(token)

// ✅ Identity endpoints
identityApi.getUser(user_id)
identityApi.updateUser(user_id, {...})
identityApi.listUsers()
identityApi.assignRole(user_id, "admin")
identityApi.deactivateUser(user_id)

// ✅ KYC endpoints
kycApi.runOcr(idFront, idBack, utilityBill)
kycApi.submitKyc(user_id, {...})
kycApi.getStatus(user_id)
kycApi.listSubmissions()
kycApi.approve(kyc_id)
kycApi.reject(kyc_id, "reason")
kycApi.flag(kyc_id, "reason")

// ✅ Consent endpoints
consentApi.grant(user_id, client_id, scopes)
consentApi.revoke(user_id, client_id)
consentApi.listForUser(user_id)

// ✅ Apps endpoints
appsApi.register({...})
appsApi.list()
appsApi.get(app_id)
appsApi.update(app_id, {...})
appsApi.approve(app_id)
appsApi.deactivate(app_id)
appsApi.rotateApiKey(app_id)
appsApi.rotateSecret(app_id)
appsApi.marketplace()
appsApi.mine()

// ✅ Webhooks endpoints
webhooksApi.subscribe(client_id, event_type, url)
webhooksApi.deactivate(sub_id)
webhooksApi.listSubscriptions()
webhooksApi.listDeliveries()
webhooksApi.retry(delivery_id)

// ✅ Session endpoints
sessionApi.listActive()
sessionApi.revoke(token_id)
sessionApi.revokeAll()

// ✅ Trust endpoints
trustApi.getProfile()
trustApi.evaluate()
```

**Automated Test:**
```bash
cd frontend/frontend
npm run test:api  # If test suite exists
```

---

## Task 9.2: Frontend Environment Configuration

**Update Frontend `.env`:**
```bash
# frontend/frontend/.env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=TrustLayer ID
VITE_APP_VERSION=1.0.0
```

**Verify API Client:**
```typescript
// frontend/frontend/src/services/api.ts
const BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
```

---

# PHASE 10: DEMO PREPARATION (Priority: CRITICAL)

**Time Estimate:** 2-3 hours

---

## Task 10.1: Seed Demo Data

**Run Seeding:**
```bash
cd frontend/backend

# Ensure database is clean
docker-compose down -v
docker-compose up -d

# Wait for database
sleep 10

# Run migrations
alembic upgrade head

# Seed data
python seed.py
```

**Verify Seed Data:**
```sql
-- Connect to database
psql -h localhost -U postgres -d unified_identity_hub

-- Check users
SELECT id, name, email, role FROM users;

-- Check KYC applications
SELECT id, user_id, status, tier, trust_score FROM kyc_applications;

-- Check registered apps
SELECT id, name, client_id, status, category FROM registered_apps;

-- Check trust profiles
SELECT user_id, trust_score, kyc_tier FROM trust_profiles;
```

---

## Task 10.2: Create Demo Script

**Demo Flow:**

### Scene 1: User Onboarding (5 minutes)
```
1. Open frontend: http://localhost:5173
2. Click "Register"
3. Fill form:
   - Email: demo@trustlayer.io
   - Username: demo_user
   - Password: Demo123!
   - Full name: Demo User
4. Submit → Show success message
5. Navigate to Dashboard → Show unverified state
```

### Scene 2: KYC Verification (7 minutes)
```
1. Navigate to "eKYC" page
2. Upload documents:
   - ID front (sample image)
   - ID back (sample image)
   - Utility bill (sample image)
3. Click "Process with AI" → Show OCR extraction
4. Review extracted data:
   - Full name
   - Date of birth
   - ID number
   - Address
5. Submit KYC application
6. Switch to Admin account (admin@fininfra.io / admin123)
7. Navigate to eKYC admin view
8. Approve KYC → Assign Tier 3
9. Switch back to demo user
10. Show updated trust score (Dashboard)
```

### Scene 3: App Marketplace (5 minutes)
```
1. Navigate to "App Marketplace"
2. Show available apps:
   - Lending App
   - Payment App
   - Banking App
3. Click "Connect" on Lending App
4. Show consent screen (scopes: profile, email, kyc_status)
5. Approve consent
6. Redirect to app (simulated)
7. Show "My Apps" → Connected apps list
```

### Scene 4: SSO Login Flow (5 minutes)
```
1. Simulate relying party app
2. Show OIDC flow:
   - /authorize → auth code
   - /token → access token
   - /userinfo → user claims
3. Show JWT payload (jwt.io):
   - sub: user_id
   - email: demo@trustlayer.io
   - kyc_tier: tier_3
   - trust_score: 85
4. Show /introspect response:
   - active: true
   - risk_level: low
```

### Scene 5: Trust & Risk (3 minutes)
```
1. Navigate to Dashboard
2. Show trust score breakdown:
   - Email verified: +20
   - Phone verified: +15
   - KYC Tier 3: +35
   - Biometric verified: +15
   - Total: 85/100
3. Show risk level: LOW
```

### Scene 6: Consent Management (3 minutes)
```
1. Navigate to "Consent" page
2. Show active consents
3. Revoke consent for one app
4. Show webhook delivery (admin view)
5. Show app loses access
```

### Scene 7: Admin Features (5 minutes)
```
1. Login as admin
2. Navigate to Biometric page → Show verification queue
3. Navigate to SSO page → Show SSO providers
4. Navigate to Audit page → Show activity log
5. Show webhook deliveries → Retry failed delivery
```

**Total Demo Time:** ~33 minutes (leave 7 minutes for Q&A)

---

## Task 10.3: Prepare Presentation Slides

**Slide Outline:**

1. **Title Slide**
   - TrustLayer ID
   - Financial-Grade Identity Infrastructure

2. **Problem Statement**
   - Repeated KYC across institutions
   - Fragmented identity
   - Security vs UX trade-off

3. **Solution Overview**
   - Portable KYC
   - Federated SSO
   - Trust scoring
   - Consent-driven sharing

4. **Architecture Diagram**
   - Frontend (React)
   - Backend (FastAPI)
   - Database (PostgreSQL)
   - AI Integration (Gemini)

5. **Key Features**
   - KYC with AI OCR
   - Trust scoring (0-100)
   - OIDC compliance
   - Webhook system
   - App marketplace

6. **Security Features**
   - RSA-256 JWT signing
   - PKCE support
   - Rate limiting
   - Webhook signing
   - Audit logging

7. **AI Integration**
   - Gemini OCR for document extraction
   - Face verification (similarity scoring)
   - Risk detection (synthetic ID probability)

8. **Trust Scoring Algorithm**
   - Email verified: +20
   - Phone verified: +15
   - KYC tier: +0/+15/+25/+35
   - Biometric: +15
   - Account age: +0 to +10

9. **Demo Flow Diagram**
   - User → KYC → Approval → App → SSO → Trust Check

10. **Technical Stack**
    - Backend: FastAPI + SQLAlchemy + PostgreSQL
    - Frontend: React + TypeScript + Tailwind
    - AI: Google Gemini 2.0 Flash
    - Auth: OIDC + OAuth2 + PKCE

11. **Scalability**
    - Modular monolith
    - Horizontal scaling ready
    - Microservices extraction path

12. **Future Roadmap**
    - Decentralized identity (DID)
    - Advanced fraud detection
    - Cross-border federation
    - Blockchain integration

13. **Live Demo**
    - (Switch to browser)

14. **Q&A**

---

# PHASE 11: RISK MITIGATION (Priority: CRITICAL)

---

## Risk 1: Database Connection Failure

**Mitigation:**
```python
# app/database.py
from sqlalchemy.exc import OperationalError

async def ensure_database_connection():
    """Verify database is accessible."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise RuntimeError("Database unavailable")

# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_database_connection()
    logger.info("Database connection verified")
    yield
```

---

## Risk 2: JWT Key Loading Failure

**Mitigation:**
```python
# app/config.py
@property
def jwt_private_key(self) -> str:
    try:
        path = Path(__file__).parent.parent / self.JWT_PRIVATE_KEY_PATH
        if not path.exists():
            raise FileNotFoundError(f"Private key not found: {path}")
        return path.read_text()
    except Exception as e:
        logger.error(f"Failed to load JWT private key: {e}")
        raise RuntimeError("JWT private key unavailable")
```

---

## Risk 3: Gemini API Failure

**Mitigation:**
```python
# app/services/ocr_service.py

async def extract_with_gemini(image_data: bytes) -> dict:
    """Extract data from document image using Gemini AI."""
    try:
        # ... Gemini API call ...
        return extracted_data
    except Exception as e:
        logger.warning(f"Gemini OCR failed: {e}")
        # Fallback to basic extraction
        return {
            "success": False,
            "extracted": {},
            "warnings": ["AI OCR unavailable, manual review required"],
            "model_used": "fallback",
        }
```

---

## Risk 4: Frontend Build Failure

**Mitigation:**
```bash
# Test frontend build
cd frontend/frontend
npm install
npm run build

# Verify build output
ls -la dist/
```

---

# PHASE 12: FINAL VERIFICATION CHECKLIST

---

## ✅ Security Checklist

- [ ] JWT signing uses RSA-256
- [ ] Private key stored securely (not in git)
- [ ] Public key accessible via `/oauth/.well-known/jwks.json`
- [ ] Rate limiting enabled on sensitive endpoints
- [ ] CORS restricted to known origins
- [ ] Security headers added (X-Frame-Options, etc.)
- [ ] HTTPS enforced in production
- [ ] Webhook payloads signed with HMAC
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (parameterized queries)

---

## ✅ Functionality Checklist

- [ ] User registration works
- [ ] Email verification works
- [ ] Password reset works
- [ ] Login returns valid JWT
- [ ] KYC submission works
- [ ] OCR extraction works (Gemini)
- [ ] KYC approval updates trust score
- [ ] App registration works
- [ ] App approval works
- [ ] OIDC authorize flow works
- [ ] OIDC token exchange works
- [ ] OIDC userinfo works
- [ ] Token introspection works
- [ ] Consent grant works
- [ ] Consent revocation works
- [ ] Webhook subscription works
- [ ] Webhook delivery works
- [ ] Session management works
- [ ] Trust score calculation works
- [ ] Dashboard loads data
- [ ] Audit log records events

---

## ✅ Performance Checklist

- [ ] API response time < 300ms (average)
- [ ] Token issuance < 200ms
- [ ] Database connection pooling configured
- [ ] N+1 queries eliminated (eager loading)
- [ ] Caching enabled for marketplace
- [ ] Async operations used throughout

---

## ✅ Integration Checklist

- [ ] Frontend connects to backend
- [ ] All API endpoints return expected shapes
- [ ] Authentication flow works end-to-end
- [ ] File uploads work (KYC documents)
- [ ] WebSocket connections work (if applicable)
- [ ] Error messages display correctly

---

## ✅ Demo Checklist

- [ ] Seed data loaded
- [ ] Demo accounts created
- [ ] Sample apps pre-approved
- [ ] Demo script prepared
- [ ] Presentation slides ready
- [ ] Backup plan if live demo fails (video recording)

---

# 🛠️ Quick Start Guide (For Team)

---

## Setup (First Time)

```bash
# 1. Clone repo (if needed)
git clone <repo-url>
cd trustIdLayer

# 2. Generate RSA keys
cd frontend/backend
mkdir -p keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start database
docker-compose up -d

# 5. Run migrations
alembic upgrade head

# 6. Seed data
python seed.py

# 7. Start backend
uvicorn app.main:app --reload --port 8000

# 8. Start frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

---

## Daily Development Workflow

```bash
# Start backend
cd frontend/backend
docker-compose up -d
uvicorn app.main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend/frontend
npm run dev

# Access:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

---

## Testing Workflow

```bash
# Backend tests
cd frontend/backend
pytest tests/ -v

# Frontend tests
cd frontend/frontend
npm run test

# Integration tests
npm run test:e2e
```

---

# 📊 Success Metrics

---

## Demo Success Criteria

1. ✅ **User can register and complete KYC** (< 2 minutes)
2. ✅ **OCR extracts data accurately** (> 90% confidence)
3. ✅ **Trust score updates in real-time** (< 1 second)
4. ✅ **SSO login works seamlessly** (< 5 seconds)
5. ✅ **Consent management is intuitive** (< 30 seconds to revoke)
6. ✅ **Admin can approve KYC** (< 1 minute)
7. ✅ **Webhooks deliver reliably** (< 5 seconds)
8. ✅ **Dashboard shows accurate data** (real-time updates)

---

## Technical Success Criteria

1. ✅ **All API endpoints return 2xx** (except intentional errors)
2. ✅ **JWT tokens verify with RSA** (check at jwt.io)
3. ✅ **Rate limiting blocks excessive requests** (test with curl)
4. ✅ **Database queries optimized** (no N+1 queries)
5. ✅ **Error responses are standardized** (ErrorResponse schema)
6. ✅ **Health check passes** (200 OK)
7. ✅ **Frontend builds without errors** (`npm run build`)
8. ✅ **Docker containers start successfully** (`docker-compose up`)

---

# 🎯 Priority Matrix

## Must Have (Before Demo)
1. ✅ RSA JWT signing
2. ✅ Rate limiting
3. ✅ CORS restriction
4. ✅ Error handling
5. ✅ Health checks
6. ✅ Seed data
7. ✅ Frontend integration test

## Should Have (Nice to Have)
1. ⚠️ Comprehensive tests
2. ⚠️ Performance optimization
3. ⚠️ Enhanced logging
4. ⚠️ API documentation
5. ⚠️ Monitoring setup

## Could Have (Post-Demo)
1. ⏳ Microservices extraction
2. ⏳ Event sourcing
3. ⏳ Advanced fraud detection
4. ⏳ Blockchain integration

---

# 🚨 Rollback Plan

If upgrades cause issues:

```bash
# 1. Revert to HMAC JWT
git checkout app/config.py
git checkout app/services/oidc_service.py
git checkout app/services/auth_service.py

# 2. Restart services
docker-compose restart

# 3. Test basic flow
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@fininfra.io","password":"admin123"}'
```

---

# 📞 Support & Troubleshooting

## Common Issues

### Issue 1: JWT Verification Fails
**Symptom:** 401 Unauthorized on all authenticated endpoints  
**Solution:**
```bash
# Verify keys are loaded
python -c "from app.config import settings; print(settings.jwt_public_key[:50])"

# Check algorithm
python -c "from app.config import settings; print(settings.JWT_ALGORITHM)"
```

### Issue 2: Database Connection Fails
**Symptom:** 500 Internal Server Error on startup  
**Solution:**
```bash
# Check database is running
docker-compose ps

# Check connection string
python -c "from app.config import settings; print(settings.DATABASE_URL)"

# Test connection
psql -h localhost -U postgres -d unified_identity_hub -c "SELECT 1"
```

### Issue 3: Frontend Can't Connect
**Symptom:** Network errors in browser console  
**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS configuration
curl -H "Origin: http://localhost:5173" -I http://localhost:8000/health

# Verify API base URL in frontend
cat frontend/frontend/.env | grep VITE_API_BASE_URL
```

### Issue 4: OCR Fails
**Symptom:** OCR endpoint returns error  
**Solution:**
```bash
# Check Gemini API key
python -c "from app.config import settings; print(settings.GEMINI_API_KEY[:10])"

# Test Gemini connection
python -c "
from google import genai
client = genai.Client(api_key='YOUR_KEY')
print(client.models.list())
"
```

---

# ✅ Final Checklist (Before Demo)

## Day Before Demo
- [ ] All code changes committed
- [ ] Database seeded with demo data
- [ ] Demo accounts tested (login works)
- [ ] Sample apps pre-approved
- [ ] Presentation slides finalized
- [ ] Demo script rehearsed (2-3 times)
- [ ] Backup plan prepared (video recording)
- [ ] Team roles assigned (presenter, operator, Q&A)

## 1 Hour Before Demo
- [ ] Start all services (backend, frontend, database)
- [ ] Verify health check passes
- [ ] Test login with demo account
- [ ] Test KYC flow (upload → OCR → approve)
- [ ] Test SSO flow (authorize → token → userinfo)
- [ ] Clear browser cache
- [ ] Open all necessary tabs
- [ ] Close unnecessary applications

## 5 Minutes Before Demo
- [ ] Restart services (fresh state)
- [ ] Verify all endpoints respond
- [ ] Open frontend in browser
- [ ] Open API docs in separate tab
- [ ] Open database client (for data verification)
- [ ] Test microphone/screen sharing

---

# 🎉 Success Criteria

## Demo is Successful If:
1. ✅ All flows complete without errors
2. ✅ OCR extraction impresses audience
3. ✅ Trust scoring is clearly explained
4. ✅ SSO flow is seamless
5. ✅ Security features are highlighted (RSA, PKCE)
6. ✅ Questions are answered confidently
7. ✅ Judges understand the value proposition

## Bonus Points:
- ⭐ Show webhook delivery in real-time
- ⭐ Show audit log capturing all actions
- ⭐ Show consent revocation → app loses access
- ⭐ Show risk level changes dynamically
- ⭐ Show admin approval workflow

---

# 🚀 Post-Demo Actions

## If Demo is Successful:
1. Collect feedback from judges
2. Document lessons learned
3. Plan production roadmap
4. Refactor toward Clean Architecture (if needed)
5. Add comprehensive test suite
6. Implement monitoring (Prometheus, Grafana)
7. Deploy to staging environment
8. Conduct security audit
9. Plan microservices extraction

## If Demo Needs Improvement:
1. Identify pain points
2. Prioritize fixes
3. Iterate quickly
4. Re-demo internally
5. Adjust presentation

---

# 📝 Summary

**Recommended Path:**
1. ✅ Use Backend #2 (`./frontend/backend`)
2. ✅ Upgrade JWT to RSA-256 (1-2 hours)
3. ✅ Add rate limiting (1 hour)
4. ✅ Enhance error handling (1 hour)
5. ✅ Test integration (1 hour)
6. ✅ Prepare demo (2-3 hours)

**Total Time:** 6-9 hours

**Result:**
- Production-grade security
- Feature-complete system
- Zero frontend integration work
- AI differentiation (Gemini OCR)
- Rich demo experience

**Confidence Level:** HIGH

---

**Document Status:** ✅ Complete  
**Next Step:** Begin Phase 1 (Security Hardening)  
**Owner:** Development Team  
**Deadline:** Before Demo Day
