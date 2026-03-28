"""
SQLAlchemy implementation of TrustRepository.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.trust.domain.repositories.trust_repository import TrustRepository
from app.modules.trust.infrastructure.persistence.trust_model import TrustModel


class SQLAlchemyTrustRepository(TrustRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, profile: TrustProfile) -> TrustProfile:
        model = TrustModel(
            id=uuid.UUID(profile.id),
            user_id=uuid.UUID(profile.user_id),
            trust_score=profile.trust_score,
            kyc_tier=profile.kyc_tier,
            face_verified=bool(profile.face_verified),
            voice_verified=bool(profile.voice_verified),
            digital_identity_active=bool(profile.digital_identity_active),
            factors=profile.factors,
            last_evaluated=profile.last_evaluated,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_user_id(self, user_id: str) -> Optional[TrustProfile]:
        result = await self.session.execute(
            select(TrustModel).where(TrustModel.user_id == uuid.UUID(user_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, profile: TrustProfile) -> TrustProfile:
        result = await self.session.execute(
            select(TrustModel).where(TrustModel.user_id == uuid.UUID(profile.user_id))
        )
        model = result.scalar_one()
        
        model.trust_score = profile.trust_score
        model.kyc_tier = profile.kyc_tier
        model.face_verified = bool(profile.face_verified)
        model.voice_verified = bool(profile.voice_verified)
        model.digital_identity_active = bool(profile.digital_identity_active)
        model.factors = profile.factors
        model.last_evaluated = profile.last_evaluated
        
        await self.session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: TrustModel) -> TrustProfile:
        return TrustProfile(
            id=str(model.id),
            user_id=str(model.user_id),
            trust_score=model.trust_score,
            kyc_tier=model.kyc_tier,
            face_verified=bool(model.face_verified),
            voice_verified=bool(model.voice_verified),
            digital_identity_active=bool(model.digital_identity_active),
            factors=model.factors or {},
            last_evaluated=model.last_evaluated,
        )
