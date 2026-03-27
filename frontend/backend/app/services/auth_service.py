import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RefreshToken
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.utils.audit import write_audit_entry


async def authenticate_user(db: AsyncSession, email_or_username: str, password: str) -> User:
    """Accept email, username, or email-format string."""
    from sqlalchemy import or_
    result = await db.execute(
        select(User).where(
            or_(User.email == email_or_username, User.username == email_or_username)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


async def create_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id), extra={"role": user.role})
    raw_refresh, expires_at = create_refresh_token()
    db_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token=raw_refresh,
        expires_at=expires_at,
    )
    db.add(db_token)
    await write_audit_entry(
        db,
        action="User Login",
        actor_id=user.id,
        actor_name=user.name,
        target=user.email,
        details=f"Login successful for {user.email}",
    )
    return access_token, raw_refresh


async def refresh_access_token(db: AsyncSession, raw_token: str) -> str:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == raw_token, RefreshToken.is_revoked == False)
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return create_access_token(str(user.id), extra={"role": user.role})


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == raw_token))
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def create_user(db: AsyncSession, name: str, email: str, password: str, role: str = "user") -> User:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        id=uuid.uuid4(),
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    return user
