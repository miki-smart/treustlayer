"""
Shared API dependencies for authentication, authorization, and database access.
"""
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import http_forbidden, http_unauthorized
from app.core.security import decode_token

# Alias for module routers that still depend on the legacy name.
get_db = get_async_session


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None
) -> str:
    """
    Extract and validate JWT from Authorization header.
    Returns user_id (sub claim).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise http_unauthorized("Missing or invalid Authorization header")
    
    token = authorization.removeprefix("Bearer ")
    
    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise http_unauthorized("Invalid token: missing sub claim")
        return user_id
    except JWTError:
        raise http_unauthorized("Invalid or expired token")


async def get_current_user_role(
    authorization: Annotated[str | None, Header()] = None
) -> str:
    """
    Extract user role from JWT.
    Returns role claim.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise http_unauthorized("Missing or invalid Authorization header")
    
    token = authorization.removeprefix("Bearer ")
    
    try:
        payload = decode_token(token)
        role: str | None = payload.get("role")
        if not role:
            raise http_unauthorized("Invalid token: missing role claim")
        return role
    except JWTError:
        raise http_unauthorized("Invalid or expired token")


async def require_admin(
    role: Annotated[str, Depends(get_current_user_role)]
) -> None:
    """Require admin role."""
    if role != "admin":
        raise http_forbidden("Admin access required")


async def require_kyc_approver(
    role: Annotated[str, Depends(get_current_user_role)]
) -> None:
    """Require admin or kyc_approver role."""
    if role not in ["admin", "kyc_approver"]:
        raise http_forbidden("KYC approver access required")


DBSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentUserRole = Annotated[str, Depends(get_current_user_role)]
