"""
Session management endpoints — lets users view and revoke their active sessions.
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_async_session
from app.modules.session.infrastructure.persistence.refresh_token_repository_impl import (
    SQLAlchemyRefreshTokenRepository,
)

router = APIRouter(prefix="/session", tags=["Session"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class ActiveSessionResponse(BaseModel):
    id: str
    client_id: str
    scopes: List[str]
    expires_at: datetime
    created_at: datetime


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/me/active",
    response_model=List[ActiveSessionResponse],
    summary="List active sessions for the current user",
)
async def list_active_sessions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyRefreshTokenRepository(session)
    tokens = await repo.list_active_for_user(user_id, skip=skip, limit=limit)
    return [
        ActiveSessionResponse(
            id=t.id,
            client_id=t.client_id,
            scopes=t.scopes,
            expires_at=t.expires_at,
            created_at=t.created_at,
        )
        for t in tokens
    ]


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a specific session by token ID",
)
async def revoke_session(
    token_id: str,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyRefreshTokenRepository(session)
    # Verify the token belongs to the requesting user before revoking
    tokens = await repo.list_active_for_user(user_id, skip=0, limit=200)
    if not any(t.id == token_id for t in tokens):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or does not belong to current user",
        )
    await repo.revoke_by_id(token_id)
    await session.commit()


@router.post(
    "/revoke-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all active sessions for the current user",
)
async def revoke_all_sessions(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyRefreshTokenRepository(session)
    await repo.revoke_all_for_user(user_id)
    await session.commit()
