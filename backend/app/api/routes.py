from fastapi import APIRouter

from app.modules.auth.presentation.api.auth_router import router as auth_router
from app.modules.identity.presentation.api.identity_router import router as identity_router
from app.modules.kyc.presentation.api.kyc_router import router as kyc_router
from app.modules.consent.presentation.api.consent_router import router as consent_router
from app.modules.app_registry.presentation.api.app_registry_router import router as app_registry_router
from app.modules.webhook.presentation.api.webhook_router import router as webhook_router
from app.modules.session.presentation.api.session_router import router as session_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(identity_router)
api_router.include_router(auth_router)
api_router.include_router(kyc_router)
api_router.include_router(consent_router)
api_router.include_router(app_registry_router)
api_router.include_router(webhook_router)
api_router.include_router(session_router)
