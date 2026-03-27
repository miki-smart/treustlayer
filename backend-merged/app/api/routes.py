"""
Main API router aggregation.

All module routers are registered here with /api/v1 prefix.
"""
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


def register_module_routers():
    """
    Register all module routers.
    Will be populated as modules are implemented.
    """
    try:
        from app.modules.identity.presentation.api.identity_router import router as identity_router
        api_router.include_router(identity_router, prefix="/identity", tags=["Identity"])
    except ImportError:
        pass
    
    try:
        from app.modules.auth.presentation.api.auth_router import router as auth_router
        api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
    except ImportError:
        pass
    
    try:
        from app.modules.kyc.presentation.api.kyc_router import router as kyc_router
        api_router.include_router(kyc_router, prefix="/kyc", tags=["KYC"])
    except ImportError:
        pass
    
    try:
        from app.modules.trust.presentation.api.trust_router import router as trust_router
        api_router.include_router(trust_router, prefix="/trust", tags=["Trust"])
    except ImportError:
        pass
    
    try:
        from app.modules.biometric.presentation.api.biometric_router import router as biometric_router
        api_router.include_router(biometric_router, prefix="/biometric", tags=["Biometric"])
    except ImportError:
        pass
    
    try:
        from app.modules.digital_identity.presentation.api.identity_router import router as identity_router
        api_router.include_router(identity_router, prefix="/identity", tags=["Digital Identity"])
    except ImportError:
        pass
    
    try:
        from app.modules.consent.presentation.api.consent_router import router as consent_router
        api_router.include_router(consent_router, prefix="/consent", tags=["Consent"])
    except ImportError:
        pass
    
    try:
        from app.modules.app_registry.presentation.api.app_router import router as app_router
        api_router.include_router(app_router, prefix="/apps", tags=["Apps"])
    except ImportError:
        pass
    
    try:
        from app.modules.session.presentation.api.session_router import router as session_router
        api_router.include_router(session_router, prefix="/session", tags=["Session"])
    except ImportError:
        pass
    
    try:
        from app.modules.webhook.presentation.api.webhook_router import router as webhook_router
        api_router.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
    except ImportError:
        pass
    
    try:
        from app.modules.dashboard.presentation.api.dashboard_router import router as dashboard_router
        api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
    except ImportError:
        pass
    
    try:
        from app.modules.audit.presentation.api.audit_router import router as audit_router
        api_router.include_router(audit_router, prefix="/audit", tags=["Audit"])
    except ImportError:
        pass


register_module_routers()
