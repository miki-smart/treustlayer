"""
Global FastAPI dependencies.
This is the composition root for cross-module service injection.
"""
from typing import List

from fastapi import Depends, Header, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import ForbiddenError, http_unauthorized
from app.core.security import decode_token, hash_secret
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService
from app.modules.app_registry.infrastructure.persistence.app_repository_impl import SQLAlchemyAppRepository
from app.modules.consent.application.services.consent_service import ConsentService
from app.modules.consent.infrastructure.persistence.consent_repository_impl import SQLAlchemyConsentRepository
from app.modules.identity.application.services.identity_service import IdentityService
from app.modules.identity.domain.entities.user import UserRole
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.application.services.kyc_service import KYCService
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.session.application.services.session_service import SessionService
from app.modules.session.infrastructure.persistence.refresh_token_repository_impl import SQLAlchemyRefreshTokenRepository

bearer_scheme = HTTPBearer(auto_error=False)


# ── Service factory dependencies ─────────────────────────────────────────────

def get_identity_service(
    session: AsyncSession = Depends(get_async_session),
) -> IdentityService:
    return IdentityService(SQLAlchemyUserRepository(session))


def get_kyc_service(
    session: AsyncSession = Depends(get_async_session),
) -> KYCService:
    return KYCService(SQLAlchemyKYCRepository(session))


def get_app_registry_service(
    session: AsyncSession = Depends(get_async_session),
) -> AppRegistryService:
    return AppRegistryService(SQLAlchemyAppRepository(session))


def get_consent_service(
    session: AsyncSession = Depends(get_async_session),
) -> ConsentService:
    return ConsentService(SQLAlchemyConsentRepository(session))


def get_session_service(
    session: AsyncSession = Depends(get_async_session),
) -> SessionService:
    return SessionService(SQLAlchemyRefreshTokenRepository(session))


# ── User JWT auth dependencies ────────────────────────────────────────────────

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Extract and validate user_id from the Bearer JWT."""
    if not credentials:
        raise http_unauthorized("No credentials provided")
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise http_unauthorized("Token missing subject")
        return user_id
    except JWTError:
        raise http_unauthorized("Invalid or expired token")


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Extract user role from the Bearer JWT."""
    if not credentials:
        raise http_unauthorized("No credentials provided")
    try:
        payload = decode_token(credentials.credentials)
        return payload.get("role", UserRole.USER.value)
    except JWTError:
        raise http_unauthorized("Invalid or expired token")


def require_role(*roles: UserRole):
    """Dependency factory — raises 403 if the caller's role is not in `roles`."""
    async def _check(
        current_role: str = Depends(get_current_user_role),
    ) -> str:
        if current_role not in {r.value for r in roles}:
            raise ForbiddenError(
                f"Requires one of roles: {[r.value for r in roles]}"
            )
        return current_role
    return _check


# ── App API-key auth dependency ───────────────────────────────────────────────

async def get_app_by_api_key(
    x_api_key: str = Header(..., description="Application API key (tl_...)"),
    session: AsyncSession = Depends(get_async_session),
):
    """Validate X-Api-Key header and return the authenticated RegisteredApp."""
    key_hash = hash_secret(x_api_key)
    repo = SQLAlchemyAppRepository(session)
    app = await repo.get_by_api_key_hash(key_hash)
    if not app:
        raise http_unauthorized("Invalid or missing API key")
    return app


async def get_token_scopes(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> List[str]:
    """Return the list of scopes from the Bearer JWT."""
    if not credentials:
        return []
    try:
        payload = decode_token(credentials.credentials)
        return payload.get("scopes", [])
    except JWTError:
        return []



# ── Service factory dependencies ─────────────────────────────────────────────

def get_identity_service(
    session: AsyncSession = Depends(get_async_session),
) -> IdentityService:
    return IdentityService(SQLAlchemyUserRepository(session))


def get_kyc_service(
    session: AsyncSession = Depends(get_async_session),
) -> KYCService:
    return KYCService(SQLAlchemyKYCRepository(session))


def get_app_registry_service(
    session: AsyncSession = Depends(get_async_session),
) -> AppRegistryService:
    return AppRegistryService(SQLAlchemyAppRepository(session))


def get_consent_service(
    session: AsyncSession = Depends(get_async_session),
) -> ConsentService:
    return ConsentService(SQLAlchemyConsentRepository(session))


def get_session_service(
    session: AsyncSession = Depends(get_async_session),
) -> SessionService:
    return SessionService(SQLAlchemyRefreshTokenRepository(session))


# ── Auth dependencies ────────────────────────────────────────────────────────

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Extract and validate user_id from the Bearer JWT."""
    if not credentials:
        raise http_unauthorized("No credentials provided")
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise http_unauthorized("Token missing subject")
        return user_id
    except JWTError:
        raise http_unauthorized("Invalid or expired token")


async def get_token_scopes(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> list[str]:
    """Return the list of scopes from the Bearer JWT."""
    if not credentials:
        return []
    try:
        payload = decode_token(credentials.credentials)
        return payload.get("scopes", [])
    except JWTError:
        return []
