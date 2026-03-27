"""
Consent router — consent management.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from app.api.dependencies import DBSession, CurrentUserId

router = APIRouter()


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    scopes: List[str]
    is_active: bool
    granted_at: str


@router.post("/grant", status_code=201)
async def grant_consent(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Grant consent. Stub implementation."""
    return {"message": "Consent granted"}


@router.post("/revoke", status_code=204)
async def revoke_consent(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Revoke consent. Stub implementation."""
    return None


@router.get("/user/{user_id}", response_model=List[ConsentResponse])
async def list_user_consents(
    user_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """List user consents. Stub implementation."""
    return []
