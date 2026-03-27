from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.kyc.domain.entities.kyc_verification import KYCStatus, KYCTier, KYCVerification
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository
from app.modules.kyc.infrastructure.persistence.kyc_model import KYCVerificationModel


class SQLAlchemyKYCRepository(KYCRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, kyc: KYCVerification) -> KYCVerification:
        model = KYCVerificationModel(
            id=kyc.id,
            user_id=kyc.user_id,
            status=kyc.status.value,
            tier=kyc.tier.value,
            trust_score=kyc.trust_score,
            document_type=kyc.document_type,
            document_number=kyc.document_number,
            document_url=kyc.document_url,
            face_similarity_score=kyc.face_similarity_score,
            rejection_reason=kyc.rejection_reason,
            verified_at=kyc.verified_at,
            created_at=kyc.created_at,
            updated_at=kyc.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, kyc_id: str) -> Optional[KYCVerification]:
        result = await self._session.execute(
            select(KYCVerificationModel).where(KYCVerificationModel.id == kyc_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(self, user_id: str) -> Optional[KYCVerification]:
        result = await self._session.execute(
            select(KYCVerificationModel).where(
                KYCVerificationModel.user_id == user_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_status(
        self, status: KYCStatus, skip: int = 0, limit: int = 50
    ) -> list[KYCVerification]:
        result = await self._session.execute(
            select(KYCVerificationModel)
            .where(KYCVerificationModel.status == status.value)
            .order_by(KYCVerificationModel.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 50) -> list[KYCVerification]:
        result = await self._session.execute(
            select(KYCVerificationModel)
            .order_by(KYCVerificationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, kyc: KYCVerification) -> KYCVerification:
        model = await self._session.get(KYCVerificationModel, kyc.id)
        if not model:
            raise ValueError(f"KYCVerification {kyc.id} not found")
        model.status = kyc.status.value
        model.tier = kyc.tier.value
        model.trust_score = kyc.trust_score
        model.document_type = kyc.document_type
        model.document_number = kyc.document_number
        model.document_url = kyc.document_url
        model.face_similarity_score = kyc.face_similarity_score
        model.rejection_reason = kyc.rejection_reason
        model.verified_at = kyc.verified_at
        model.updated_at = kyc.updated_at
        await self._session.flush()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: KYCVerificationModel) -> KYCVerification:
        return KYCVerification(
            id=str(model.id),
            user_id=str(model.user_id),
            status=KYCStatus(model.status),
            tier=KYCTier(model.tier),
            trust_score=model.trust_score,
            document_type=model.document_type,
            document_number=model.document_number,
            document_url=model.document_url,
            face_similarity_score=model.face_similarity_score,
            rejection_reason=model.rejection_reason,
            verified_at=model.verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
