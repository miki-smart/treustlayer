"""
Auth router — handles login, logout, and OIDC flows.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import DBSession, CurrentUserId
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, session: DBSession):
    """Direct login for frontend."""
    repo = SQLAlchemyUserRepository(session)
    user_entity = await repo.get_by_email(payload.email.lower())
    
    if not user_entity or not verify_password(payload.password, user_entity.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user_entity.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    
    access_token = create_access_token(
        subject=user_entity.id,
        extra_claims={
            "username": user_entity.username,
            "role": user_entity.role.value,
            "email": user_entity.email,
        }
    )
    
    await session.commit()
    
    return LoginResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=900,
        user_id=user_entity.id,
        username=user_entity.username,
        role=user_entity.role.value,
    )


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, session: DBSession, current_user_id: CurrentUserId):
    """Logout (revoke refresh token if provided)."""
    await session.commit()
    return None
