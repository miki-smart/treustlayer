"""
Audit router � audit log access.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.api.dependencies import DBSession, require_admin
from app.modules.audit.infrastructure.persistence.audit_repository_impl import SQLAlchemyAuditRepository

router = APIRouter()


class AuditEntryResponse(BaseModel):
    id: str
    actor_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    metadata: Dict[str, Any]
    changes: Dict[str, Any]
    timestamp: str


@router.get("/entries", response_model=List[AuditEntryResponse])
async def list_audit_entries(
    session: DBSession,
    _: None = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
):
    """
    List audit entries (admin only).
    
    Supports filtering by action and resource_type.
    """
    audit_repo = SQLAlchemyAuditRepository(session)
    
    if action:
        entries = await audit_repo.list_by_action(action, skip, limit)
    else:
        entries = await audit_repo.list_all(skip, limit)
    
    return [
        AuditEntryResponse(
            id=entry.id,
            actor_id=entry.actor_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            metadata=entry.metadata,
            changes=entry.changes,
            timestamp=entry.timestamp.isoformat(),
        )
        for entry in entries
    ]


@router.get("/user/{user_id}", response_model=List[AuditEntryResponse])
async def list_user_audit_entries(
    user_id: str,
    session: DBSession,
    _: None = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
):
    """
    List audit entries for a specific user (admin only).
    """
    audit_repo = SQLAlchemyAuditRepository(session)
    entries = await audit_repo.list_by_actor(user_id, skip, limit)
    
    return [
        AuditEntryResponse(
            id=entry.id,
            actor_id=entry.actor_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            metadata=entry.metadata,
            changes=entry.changes,
            timestamp=entry.timestamp.isoformat(),
        )
        for entry in entries
    ]


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditEntryResponse])
async def list_resource_audit_entries(
    resource_type: str,
    resource_id: str,
    session: DBSession,
    _: None = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
):
    """
    List audit entries for a specific resource (admin only).
    """
    audit_repo = SQLAlchemyAuditRepository(session)
    entries = await audit_repo.list_by_resource(resource_type, resource_id, skip, limit)
    
    return [
        AuditEntryResponse(
            id=entry.id,
            actor_id=entry.actor_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            metadata=entry.metadata,
            changes=entry.changes,
            timestamp=entry.timestamp.isoformat(),
        )
        for entry in entries
    ]
