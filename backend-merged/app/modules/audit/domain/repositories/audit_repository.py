"""
AuditRepository — repository interface for audit domain.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.audit.domain.entities.audit_entry import AuditEntry


class AuditRepository(ABC):
    """Repository interface for audit logs."""
    
    @abstractmethod
    async def create(self, entry: AuditEntry) -> AuditEntry:
        """Create audit entry (append-only)."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        pass
    
    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[AuditEntry]:
        """List all audit entries."""
        pass
    
    @abstractmethod
    async def list_by_actor(
        self, actor_id: str, skip: int = 0, limit: int = 100
    ) -> List[AuditEntry]:
        """List audit entries by actor."""
        pass
    
    @abstractmethod
    async def list_by_resource(
        self, resource_type: str, resource_id: str, skip: int = 0, limit: int = 100
    ) -> List[AuditEntry]:
        """List audit entries for a specific resource."""
        pass
    
    @abstractmethod
    async def list_by_action(
        self, action: str, skip: int = 0, limit: int = 100
    ) -> List[AuditEntry]:
        """List audit entries by action type."""
        pass
