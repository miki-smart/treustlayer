"""
Session management — /api/v1/session/*
Active sessions = non-revoked refresh tokens for the current user.
"""
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select, update

from app.dependencies import CurrentUser, DB
from app.models.user import RefreshToken

router = APIRouter(prefix="/session", tags=["Session"])


class ActiveSessionResponse(BaseModel):
    id: str
    client_id: str
    scopes: list[str]
    expires_at: str
    created_at: str


def _session_out(rt: RefreshToken) -> ActiveSessionResponse:
    return ActiveSessionResponse(
        id=str(rt.id),
        client_id=rt.client_id or "direct-login",
        scopes=(rt.scopes or "").split() if rt.scopes else [],
        expires_at=rt.expires_at.isoformat() if rt.expires_at else "",
        created_at=rt.created_at.isoformat() if rt.created_at else "",
    )


@router.get("/me/active", response_model=list[ActiveSessionResponse], summary="List active sessions for the current user")
async def list_active_sessions(
    current_user: CurrentUser, db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.created_at.desc())
        .offset(skip).limit(limit)
    )
    return [_session_out(rt) for rt in result.scalars().all()]


@router.delete("/{token_id}", status_code=204, summary="Revoke a specific session by token ID")
async def revoke_session(token_id: str, current_user: CurrentUser, db: DB):
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == uuid.UUID(token_id),
            RefreshToken.user_id == current_user.id,
        )
    )
    rt = result.scalar_one_or_none()
    if rt:
        rt.is_revoked = True


@router.post("/revoke-all", status_code=204, summary="Revoke all active sessions for the current user")
async def revoke_all_sessions(current_user: CurrentUser, db: DB):
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )
