"""
SQLAlchemy implementation of KYCRepository.
"""
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.kyc.domain.entities.kyc_verification import KYCVerification, KYCStatus, KYCTier
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository
from app.modules.kyc.infrastructure.persistence.kyc_model import KYCModel


class SQLAlchemyKYCRepository(KYCRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, verification: KYCVerification) -> KYCVerification:
        model = KYCModel(
            id=uuid.UUID(verification.id),
            user_id=uuid.UUID(verification.user_id),
            status=verification.status.value,
            tier=verification.tier.value,
            full_name=verification.full_name,
            date_of_birth=verification.date_of_birth,
            gender=verification.gender,
            nationality=verification.nationality,
            place_of_birth=verification.place_of_birth,
            document_type=verification.document_type,
            document_number=verification.document_number,
            issue_date=verification.issue_date,
            expiry_date=verification.expiry_date,
            address=verification.address,
            billing_name=verification.billing_name,
            service_provider=verification.service_provider,
            service_type=verification.service_type,
            bill_date=verification.bill_date,
            account_number=verification.account_number,
            mrz_line1=verification.mrz_line1,
            mrz_line2=verification.mrz_line2,
            id_front_url=verification.id_front_url,
            id_back_url=verification.id_back_url,
            utility_bill_url=verification.utility_bill_url,
            face_image_url=verification.face_image_url,
            documents_submitted=verification.documents_submitted,
            extracted_data=verification.extracted_data,
            id_ocr_confidence=verification.id_ocr_confidence,
            utility_ocr_confidence=verification.utility_ocr_confidence,
            overall_confidence=verification.overall_confidence,
            risk_score=verification.risk_score,
            synthetic_id_probability=verification.synthetic_id_probability,
            face_similarity_score=verification.face_similarity_score,
            reviewer_id=uuid.UUID(verification.reviewer_id) if verification.reviewer_id else None,
            rejection_reason=verification.rejection_reason,
            notes=verification.notes,
            submitted_at=verification.submitted_at,
            reviewed_at=verification.reviewed_at,
            verified_at=verification.verified_at,
            created_at=verification.created_at,
            updated_at=verification.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_id(self, verification_id: str) -> Optional[KYCVerification]:
        result = await self.session.execute(
            select(KYCModel).where(KYCModel.id == uuid.UUID(verification_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(self, user_id: str) -> Optional[KYCVerification]:
        result = await self.session.execute(
            select(KYCModel).where(KYCModel.user_id == uuid.UUID(user_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_status(self, status: KYCStatus, skip: int = 0, limit: int = 50) -> List[KYCVerification]:
        result = await self.session.execute(
            select(KYCModel)
            .where(KYCModel.status == status.value)
            .order_by(KYCModel.submitted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 50) -> List[KYCVerification]:
        result = await self.session.execute(
            select(KYCModel)
            .order_by(KYCModel.submitted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, verification: KYCVerification) -> KYCVerification:
        result = await self.session.execute(
            select(KYCModel).where(KYCModel.id == uuid.UUID(verification.id))
        )
        model = result.scalar_one()
        
        model.status = verification.status.value
        model.tier = verification.tier.value
        model.full_name = verification.full_name
        model.date_of_birth = verification.date_of_birth
        model.gender = verification.gender
        model.nationality = verification.nationality
        model.place_of_birth = verification.place_of_birth
        model.document_type = verification.document_type
        model.document_number = verification.document_number
        model.issue_date = verification.issue_date
        model.expiry_date = verification.expiry_date
        model.address = verification.address
        model.billing_name = verification.billing_name
        model.service_provider = verification.service_provider
        model.service_type = verification.service_type
        model.bill_date = verification.bill_date
        model.account_number = verification.account_number
        model.mrz_line1 = verification.mrz_line1
        model.mrz_line2 = verification.mrz_line2
        model.id_front_url = verification.id_front_url
        model.id_back_url = verification.id_back_url
        model.utility_bill_url = verification.utility_bill_url
        model.face_image_url = verification.face_image_url
        model.documents_submitted = verification.documents_submitted
        model.extracted_data = verification.extracted_data
        model.id_ocr_confidence = verification.id_ocr_confidence
        model.utility_ocr_confidence = verification.utility_ocr_confidence
        model.overall_confidence = verification.overall_confidence
        model.risk_score = verification.risk_score
        model.synthetic_id_probability = verification.synthetic_id_probability
        model.face_similarity_score = verification.face_similarity_score
        model.reviewer_id = uuid.UUID(verification.reviewer_id) if verification.reviewer_id else None
        model.rejection_reason = verification.rejection_reason
        model.notes = verification.notes
        model.submitted_at = verification.submitted_at
        model.reviewed_at = verification.reviewed_at
        model.verified_at = verification.verified_at
        model.updated_at = verification.updated_at
        
        await self.session.flush()
        return self._to_entity(model)

    def _to_entity(self, model: KYCModel) -> KYCVerification:
        return KYCVerification(
            id=str(model.id),
            user_id=str(model.user_id),
            status=KYCStatus(model.status),
            tier=KYCTier(model.tier),
            full_name=model.full_name,
            date_of_birth=model.date_of_birth,
            gender=model.gender,
            nationality=model.nationality,
            place_of_birth=model.place_of_birth,
            document_type=model.document_type,
            document_number=model.document_number,
            issue_date=model.issue_date,
            expiry_date=model.expiry_date,
            address=model.address,
            billing_name=model.billing_name,
            service_provider=model.service_provider,
            service_type=model.service_type,
            bill_date=model.bill_date,
            account_number=model.account_number,
            mrz_line1=model.mrz_line1,
            mrz_line2=model.mrz_line2,
            id_front_url=model.id_front_url,
            id_back_url=model.id_back_url,
            utility_bill_url=model.utility_bill_url,
            face_image_url=model.face_image_url,
            documents_submitted=model.documents_submitted or [],
            extracted_data=model.extracted_data,
            id_ocr_confidence=model.id_ocr_confidence or 0.0,
            utility_ocr_confidence=model.utility_ocr_confidence or 0.0,
            overall_confidence=model.overall_confidence or 0.0,
            risk_score=model.risk_score,
            synthetic_id_probability=model.synthetic_id_probability or 0.0,
            face_similarity_score=model.face_similarity_score,
            reviewer_id=str(model.reviewer_id) if model.reviewer_id else None,
            rejection_reason=model.rejection_reason,
            notes=model.notes,
            submitted_at=model.submitted_at,
            reviewed_at=model.reviewed_at,
            verified_at=model.verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
