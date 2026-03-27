"""
Main API router aggregation.

All module routers are mounted under ``/api/v1`` (see ``api_router``).

Registered modules (12) — each row is ``(name, import path, URL prefix, OpenAPI tags)``:

1. identity          → /identity
2. consent           → /consent
3. auth              → /auth
4. kyc               → /kyc
5. trust             → /trust
6. biometric         → /biometric
7. digital_identity  → /identity (same prefix as identity; routes merge)
8. apps              → /apps
9. session           → /session
10. webhooks         → /webhooks
11. dashboard        → /dashboard
12. audit            → /audit

Call :func:`register_module_routers` from ``main`` after ``logging.basicConfig`` so
failed imports are logged correctly. Uses :func:`importlib.import_module` so dotted
paths resolve to the intended submodule.
"""
from __future__ import annotations

import importlib
import logging
from typing import Final

from fastapi import APIRouter

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api/v1")

# (logical name, python module path, mount prefix, openapi tags)
REGISTERED_MODULES: Final[
    tuple[tuple[str, str, str, list[str]], ...]
] = (
    ("identity", "app.modules.identity.presentation.api.identity_router", "/identity", ["Identity"]),
    ("consent", "app.modules.consent.presentation.api.consent_router", "/consent", ["Consent"]),
    ("auth", "app.modules.auth.presentation.api.auth_router", "/auth", ["Auth"]),
    ("kyc", "app.modules.kyc.presentation.api.kyc_router", "/kyc", ["KYC"]),
    ("trust", "app.modules.trust.presentation.api.trust_router", "/trust", ["Trust"]),
    ("biometric", "app.modules.biometric.presentation.api.biometric_router", "/biometric", ["Biometric"]),
    (
        "digital_identity",
        "app.modules.digital_identity.presentation.api.identity_router",
        "/identity",
        ["Digital Identity"],
    ),
    ("apps", "app.modules.app_registry.presentation.api.app_router", "/apps", ["Apps"]),
    ("session", "app.modules.session.presentation.api.session_router", "/session", ["Session"]),
    ("webhooks", "app.modules.webhook.presentation.api.webhook_router", "/webhooks", ["Webhooks"]),
    ("dashboard", "app.modules.dashboard.presentation.api.dashboard_router", "/dashboard", ["Dashboard"]),
    ("audit", "app.modules.audit.presentation.api.audit_router", "/audit", ["Audit"]),
)


def _include(name: str, import_path: str, attr: str, prefix: str, tags: list[str]) -> None:
    try:
        module = importlib.import_module(import_path)
        router = getattr(module, attr)
        api_router.include_router(router, prefix=prefix, tags=tags)
    except Exception as exc:
        logger.error(
            "API router %r not registered (module=%s): %s",
            name,
            import_path,
            exc,
            exc_info=True,
        )


def register_module_routers() -> None:
    """Import and mount all module routers on ``api_router``."""
    for name, import_path, prefix, tags in REGISTERED_MODULES:
        _include(name, import_path, "router", prefix, tags)
