from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, biometric, kyc, identity, sso, cards, dashboard, audit
from app.routers import apps, oidc, trust
from app.routers import user_identity, consent, webhooks, session


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="TrustLayer ID",
    description=(
        "Production-grade modular monolith: Digital Identity, OIDC, KYC, "
        "Consent, and Event-driven trust scoring."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

# ── TrustLayer ID canonical routers ──────────────────────────────────────────
app.include_router(user_identity.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(kyc.router, prefix=API_PREFIX)
app.include_router(consent.router, prefix=API_PREFIX)
app.include_router(apps.router, prefix=API_PREFIX)
app.include_router(webhooks.router, prefix=API_PREFIX)
app.include_router(session.router, prefix=API_PREFIX)

# ── Legacy / supplemental routers (kept for backward compat) ─────────────────
app.include_router(biometric.router, prefix=API_PREFIX)
app.include_router(identity.router, prefix=API_PREFIX)
app.include_router(sso.router, prefix=API_PREFIX)
app.include_router(cards.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(oidc.router, prefix=API_PREFIX)
app.include_router(trust.router, prefix=API_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "TrustLayer ID API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
