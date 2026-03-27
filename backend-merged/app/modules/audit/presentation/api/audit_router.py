"""
Audit router — audit log access.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from app.api.dependencies import DBSession, require_admin

router = APIRouter()


class AuditEntry(BaseModel):
    id: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    timestamp: str


@router.get("/entries", response_model=List[AuditEntry])
async def list_audit_entries(
    session: DBSession,
    _: None = Depends(require_admin),
):
    """List audit entries (admin). Stub implementation."""
    return []


@router.get("/user/{user_id}", response_model=List[AuditEntry])
async def list_user_audit_entries(
    user_id: str,
    session: DBSession,
    _: None = Depends(require_admin),
):
    """List audit entries for a user (admin). Stub implementation."""
    return []
