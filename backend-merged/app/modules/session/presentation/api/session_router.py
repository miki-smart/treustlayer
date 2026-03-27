"""
Session router — refresh token management.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from app.api.dependencies import DBSession, CurrentUserId

router = APIRouter()


class ActiveSessionResponse(BaseModel):
    id: str
    client_id: str
    scopes: List[str]
    expires_at: str
    created_at: str


@router.get("/me/active", response_model=List[ActiveSessionResponse])
async def list_active_sessions(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """List active sessions. Stub implementation."""
    return []


@router.delete("/{token_id}", status_code=204)
async def revoke_session(
    token_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Revoke a session. Stub implementation."""
    return None


@router.post("/revoke-all", status_code=204)
async def revoke_all_sessions(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Sign out all devices. Stub implementation."""
    return None
