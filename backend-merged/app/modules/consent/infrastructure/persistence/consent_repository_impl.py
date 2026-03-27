"""
SQLAlchemy implementation of ConsentRepository.
"""
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consent.domain.entities.consent_record import ConsentRecord
from app.modules.consent.domain.repositories.consent_repository import ConsentRepository
from app.modules.consent.infrastructure.persistence.consent_model import (
    ConsentRecordModel,
)


class SQLAlchemyConsentRepository(ConsentRepository):
    """SQLAlchemy implementation of consent repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, consent: ConsentRecord) -> ConsentRecord:
        """Create new consent record."""
        model = ConsentRecordModel(
            id=consent.id,
            user_id=consent.user_id,
            client_id=consent.client_id,
            scopes=consent.scopes,
            is_active=consent.is_active,
            granted_at=consent.granted_at,
            revoked_at=consent.revoked_at,
        )
        self.session.add(model)
        await self.session.flush()
        return consent
    
    async def get_by_id(self, consent_id: str) -> Optional[ConsentRecord]:
        """Get consent by ID."""
        result = await self.session.execute(
            select(ConsentRecordModel).where(ConsentRecordModel.id == consent_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_entity(model)
    
    async def get_by_user_and_client(
        self, user_id: str, client_id: str
    ) -> Optional[ConsentRecord]:
        """Get consent by user and client."""
        result = await self.session.execute(
            select(ConsentRecordModel).where(
                ConsentRecordModel.user_id == user_id,
                ConsentRecordModel.client_id == client_id,
                ConsentRecordModel.is_active == True,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_entity(model)
    
    async def list_by_user(self, user_id: str) -> List[ConsentRecord]:
        """List all consents for a user."""
        result = await self.session.execute(
            select(ConsentRecordModel)
            .where(ConsentRecordModel.user_id == user_id)
            .order_by(ConsentRecordModel.granted_at.desc())
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def list_by_client(self, client_id: str) -> List[ConsentRecord]:
        """List all consents for a client."""
        result = await self.session.execute(
            select(ConsentRecordModel)
            .where(ConsentRecordModel.client_id == client_id)
            .order_by(ConsentRecordModel.granted_at.desc())
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def update(self, consent: ConsentRecord) -> ConsentRecord:
        """Update consent record."""
        result = await self.session.execute(
            select(ConsentRecordModel).where(ConsentRecordModel.id == consent.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.scopes = consent.scopes
            model.is_active = consent.is_active
            model.revoked_at = consent.revoked_at
            await self.session.flush()
        return consent
    
    async def delete(self, consent_id: str) -> None:
        """Delete consent record."""
        await self.session.execute(
            delete(ConsentRecordModel).where(ConsentRecordModel.id == consent_id)
        )
        await self.session.flush()
    
    def _model_to_entity(self, model: ConsentRecordModel) -> ConsentRecord:
        """Convert model to entity."""
        return ConsentRecord(
            id=str(model.id),
            user_id=str(model.user_id),
            client_id=model.client_id,
            scopes=model.scopes,
            is_active=model.is_active,
            granted_at=model.granted_at,
            revoked_at=model.revoked_at,
        )
