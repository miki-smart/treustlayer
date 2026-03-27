"""
AuditLogger — service for creating audit log entries.
"""
import logging
from typing import Any, Dict, Optional

from app.modules.audit.domain.entities.audit_entry import AuditEntry
from app.modules.audit.domain.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logging service.
    
    Creates immutable audit trail for compliance.
    """
    
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo
    
    async def log(
        self,
        action: str,
        resource_type: str,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """
        Create audit log entry.
        
        Args:
            action: Action performed (e.g., "user.created")
            resource_type: Type of resource (e.g., "user", "kyc")
            actor_id: User who performed action (None for system)
            resource_id: ID of affected resource
            metadata: Additional context
            changes: Before/after values
        
        Returns:
            Created audit entry
        """
        entry = AuditEntry(
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            resource_id=resource_id,
            metadata=metadata or {},
            changes=changes or {},
        )
        
        saved = await self.audit_repo.create(entry)
        
        logger.debug(f"Audit log created: {action} on {resource_type} by {actor_id or 'system'}")
        
        return saved
