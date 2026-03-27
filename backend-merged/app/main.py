"""
TrustLayer ID — Identity as a Service + Federated SSO

Merged backend combining:
- Backend #1: Clean Architecture, RSA JWT, schema isolation
- Backend #2: AI OCR, marketplace, dashboard, audit

Scope: IDaaS + Federated SSO (no cards, no biometrics)
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router, register_module_routers
from app.core.event_handlers import register_event_handlers
from app.core.exceptions import DomainError

register_module_routers()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TrustLayer ID v%s", settings.APP_VERSION)
    
    register_event_handlers()
    
    webhook_worker_task = None
    try:
        from app.modules.webhook.application.tasks.webhook_worker import run_webhook_worker, stop_webhook_worker
        webhook_worker_task = asyncio.create_task(run_webhook_worker(interval_seconds=15))
        logger.info("Webhook worker task started")
    except ImportError:
        logger.warning("Webhook worker not yet implemented")
    
    yield
    
    logger.info("Shutting down TrustLayer ID")
    if webhook_worker_task:
        try:
            from app.modules.webhook.application.tasks.webhook_worker import stop_webhook_worker
            stop_webhook_worker()
            webhook_worker_task.cancel()
            await webhook_worker_task
        except (asyncio.CancelledError, ImportError):
            pass
    logger.info("TrustLayer ID shut down cleanly")


OPENAPI_TAGS = [
    {"name": "Health", "description": "Liveness and version"},
    {"name": "Identity", "description": "Users, profiles, admin user management"},
    {"name": "Consent", "description": "OAuth2-style consent grants and revocation"},
    {"name": "Auth", "description": "Login, tokens, OIDC"},
    {"name": "KYC", "description": "Document verification"},
    {"name": "Trust", "description": "Trust scores and evaluation"},
    {"name": "Biometric", "description": "Face and voice checks"},
    {"name": "Digital Identity", "description": "Portable digital identity (DID-style)"},
    {"name": "Apps", "description": "OAuth2 client registry and marketplace"},
    {"name": "Session", "description": "Refresh tokens and device sessions"},
    {"name": "Webhooks", "description": "Subscriptions and deliveries"},
    {"name": "Dashboard", "description": "Admin analytics"},
    {"name": "Audit", "description": "Audit log queries"},
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Identity as a Service (IDaaS) + Federated SSO. "
        "Portable KYC, Trust Scoring, Consent Management, App Marketplace."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


app.include_router(api_router)


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
    return {"status": "ok", "version": settings.APP_VERSION}
