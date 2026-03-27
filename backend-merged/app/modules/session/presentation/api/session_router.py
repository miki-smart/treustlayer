"""
Session router � refresh token management.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import DBSession, CurrentUserId
from app.modules.auth.infrastructure.persistence.auth_repository_impl import SQLAlchemyAuthRepository

router = APIRouter()


class ActiveSessionResponse(BaseModel):
    id: str
    client_id: str
    scopes: List[str]
    device_info: Optional[str]
    ip_address: Optional[str]
    expires_at: str
    created_at: str
    last_used_at: Optional[str]


@router.get("/me/active", response_model=List[ActiveSessionResponse])
async def list_active_sessions(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    List active refresh tokens (sessions) for current user.
    
    Shows all devices/clients with active sessions.
    """
    auth_repo = SQLAlchemyAuthRepository(session)
    tokens = await auth_repo.list_user_tokens(current_user_id)
    
    return [
        ActiveSessionResponse(
            id=token.id,
            client_id=token.client_id,
            scopes=token.scopes,
            device_info=token.device_info,
            ip_address=token.ip_address,
            expires_at=token.expires_at.isoformat(),
            created_at=token.created_at.isoformat(),
            last_used_at=token.last_used_at.isoformat() if token.last_used_at else None,
        )
        for token in tokens
    ]


@router.delete("/{token_id}", status_code=204)
async def revoke_session(
    token_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Revoke a specific session (refresh token).
    
    Signs out a specific device/client.
    """
    auth_repo = SQLAlchemyAuthRepository(session)
    
    # Verify token belongs to current user
    tokens = await auth_repo.list_user_tokens(current_user_id)
    if not any(t.id == token_id for t in tokens):
        raise HTTPException(status_code=404, detail="Session not found")
    
    await auth_repo.revoke_refresh_token(token_id)
    await session.commit()
    
    return None


@router.post("/revoke-all", status_code=204)
async def revoke_all_sessions(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Revoke all sessions (refresh tokens) for current user.
    
    Signs out all devices/clients.
    """
    auth_repo = SQLAlchemyAuthRepository(session)
    await auth_repo.revoke_all_user_tokens(current_user_id)
    await session.commit()
    
    return None
