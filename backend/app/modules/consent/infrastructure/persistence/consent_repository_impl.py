from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consent.domain.entities.consent import Consent
from app.modules.consent.domain.repositories.consent_repository import ConsentRepository
from app.modules.consent.infrastructure.persistence.consent_model import ConsentModel


class SQLAlchemyConsentRepository(ConsentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, consent: Consent) -> Consent:
        model = ConsentModel(
            id=consent.id,
            user_id=consent.user_id,
            client_id=consent.client_id,
            scopes=consent.scopes,
            is_active=consent.is_active,
            granted_at=consent.granted_at,
            revoked_at=consent.revoked_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_active(self, user_id: str, client_id: str) -> Optional[Consent]:
        result = await self._session.execute(
            select(ConsentModel).where(
                and_(
                    ConsentModel.user_id == user_id,
                    ConsentModel.client_id == client_id,
                    ConsentModel.is_active.is_(True),
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all_for_user(self, user_id: str) -> List[Consent]:
        result = await self._session.execute(
            select(ConsentModel).where(
                and_(ConsentModel.user_id == user_id, ConsentModel.is_active.is_(True))
            )
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def revoke(self, consent_id: str) -> None:
        await self._session.execute(
            update(ConsentModel)
            .where(ConsentModel.id == consent_id)
            .values(is_active=False, revoked_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    async def update(self, consent: Consent) -> Consent:
        model = await self._session.get(ConsentModel, consent.id)
        if not model:
            raise ValueError(f"Consent {consent.id} not found")
        model.scopes = consent.scopes
        model.is_active = consent.is_active
        model.revoked_at = consent.revoked_at
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: ConsentModel) -> Consent:
        return Consent(
            id=str(model.id),
            user_id=str(model.user_id),
            client_id=str(model.client_id),
            scopes=list(model.scopes or []),
            is_active=bool(model.is_active),
            granted_at=model.granted_at,
            revoked_at=model.revoked_at,
        )
