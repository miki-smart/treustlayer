"""
App registry router — OAuth2 client management and marketplace.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from app.api.dependencies import DBSession, CurrentUserId, require_admin

router = APIRouter()


class AppResponse(BaseModel):
    id: str
    name: str
    client_id: str
    client_secret: str | None = None
    api_key: str | None = None
    owner_id: str | None = None
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str
    logo_url: str | None = None
    category: str
    is_active: bool
    is_approved: bool
    is_public: bool


@router.post("/", response_model=AppResponse, status_code=201)
async def register_app(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Register new app. Stub implementation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/", response_model=List[AppResponse])
async def list_apps(
    session: DBSession,
    _: None = Depends(require_admin),
):
    """List all apps (admin). Stub implementation."""
    return []


@router.get("/marketplace", response_model=List[AppResponse])
async def get_marketplace(session: DBSession):
    """Public app marketplace. Stub implementation."""
    return []


@router.get("/mine", response_model=List[AppResponse])
async def get_my_apps(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Get user's connected apps. Stub implementation."""
    return []
