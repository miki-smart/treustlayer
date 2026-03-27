"""
SQLAlchemy implementation of AuditRepository.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.domain.entities.audit_entry import AuditEntry
from app.modules.audit.domain.repositories.audit_repository import AuditRepository
from app.modules.audit.infrastructure.persistence.audit_model import AuditEntryModel


class SQLAlchemyAuditRepository(AuditRepository):
    """SQLAlchemy implementation of audit repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, entry: AuditEntry) -> AuditEntry:
        """Create audit entry (append-only)."""
        model = AuditEntryModel(
            id=entry.id,
            actor_id=entry.actor_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            metadata=entry.metadata,
            changes=entry.changes,
            timestamp=entry.timestamp,
        )
        self.session.add(model)
        await self.session.flush()
        return entry
    
    async def get_by_id(self, entry_id: str) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        result = await self.session.execute(
            select(AuditEntryModel).where(AuditEntryModel.id == entry_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_entity(model)
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[AuditEntry]:
        """List all audit entries."""
        result = await self.session.execute(
            select(AuditEntryModel)
            .order_by(AuditEntryModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def list_by_actor(
        self, actor_id: str, skip: int = 0, limit: int = 100
    ) -> List[AuditEntry]:
        """List audit entries by actor."""
        result = await self.session.execute(
            select(AuditEntryModel)
            .where(AuditEntryModel.actor_id == actor_id)
            .order_by(AuditEntryModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def list_by_resource(
        self, resource_type: str, resource_id: str, skip: int = 0, limit: int = 100
    ) -> List[AuditEntry]:
        """List audit entries for a specific resource."""
        result = await self.session.execute(
            select(AuditEntryModel)
            .where(
                AuditEntryModel.resource_type == resource_type,
                AuditEntryModel.resource_id == resource_id,
            )
            .order_by(AuditEntryModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def list_by_action(
        self, action: str, skip: int = 0, limit: int = 100
    ) -> List[AuditEntry]:
        """List audit entries by action type."""
        result = await self.session.execute(
            select(AuditEntryModel)
            .where(AuditEntryModel.action == action)
            .order_by(AuditEntryModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    def _model_to_entity(self, model: AuditEntryModel) -> AuditEntry:
        """Convert model to entity."""
        return AuditEntry(
            id=str(model.id),
            actor_id=str(model.actor_id) if model.actor_id else None,
            action=model.action,
            resource_type=model.resource_type,
            resource_id=str(model.resource_id) if model.resource_id else None,
            metadata=model.metadata,
            changes=model.changes,
            timestamp=model.timestamp,
        )
