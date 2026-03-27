"""
KYC use cases: submit, approve, reject.

Trust score formula (rule-based with mock AI hooks):
  - Document submitted:        +30
  - Face similarity ≥ 0.85:   +20
  - Face similarity ≥ 0.70:   +10
  - Document approved:        +40
  Total max = 90; tier upgrade thresholds captured in ApproveKYCUseCase.
"""
from app.core.events import event_bus
from app.core.exceptions import InvalidOperationError, NotFoundError
from app.modules.kyc.application.dto.kyc_dto import KYCResponseDTO, SubmitKYCDTO
from app.modules.kyc.domain.entities.kyc_verification import (
    KYCStatus,
    KYCTier,
    KYCVerification,
)
from app.modules.kyc.domain.events.kyc_events import (
    KYCApprovedEvent,
    KYCRejectedEvent,
    KYCSubmittedEvent,
    RiskUpdatedEvent,
)
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository


def _mock_face_similarity(face_image_url: str | None) -> float:
    """
    Mock AI face similarity scoring.
    Replace with a real model call (e.g. AWS Rekognition, DeepFace).
    Returns a float 0.0–1.0.
    """
    if face_image_url:
        return 0.92  # stub: always good match when URL provided
    return 0.0


def _calculate_trust_score(
    document_submitted: bool,
    face_similarity: float,
    approved: bool,
) -> int:
    score = 0
    if document_submitted:
        score += 30
    if face_similarity >= 0.85:
        score += 20
    elif face_similarity >= 0.70:
        score += 10
    if approved:
        score += 40
    return min(score, 100)


def _to_response(kyc: KYCVerification) -> KYCResponseDTO:
    return KYCResponseDTO(
        id=kyc.id,
        user_id=kyc.user_id,
        status=kyc.status.value,
        tier=kyc.tier.value,
        trust_score=kyc.trust_score,
        document_type=kyc.document_type,
        document_number=kyc.document_number,
        rejection_reason=kyc.rejection_reason,
        face_similarity_score=kyc.face_similarity_score,
    )


class SubmitKYCUseCase:
    def __init__(self, kyc_repository: KYCRepository) -> None:
        self._repo = kyc_repository

    async def execute(self, dto: SubmitKYCDTO) -> KYCResponseDTO:
        # Check for existing KYC record; create one if it does not exist
        existing = await self._repo.get_by_user_id(dto.user_id)
        if existing and existing.status == KYCStatus.APPROVED:
            raise InvalidOperationError("KYC is already approved for this user")

        face_score = _mock_face_similarity(dto.face_image_url)
        partial_score = _calculate_trust_score(
            document_submitted=True,
            face_similarity=face_score,
            approved=False,
        )

        if existing:
            existing.submit(
                document_type=dto.document_type,
                document_number=dto.document_number,
                document_url=dto.document_url,
                face_similarity_score=face_score,
            )
            existing.trust_score = partial_score
            kyc = await self._repo.update(existing)
        else:
            kyc = KYCVerification(user_id=dto.user_id)
            kyc.submit(
                document_type=dto.document_type,
                document_number=dto.document_number,
                document_url=dto.document_url,
                face_similarity_score=face_score,
            )
            kyc.trust_score = partial_score
            kyc = await self._repo.create(kyc)

        await event_bus.publish(KYCSubmittedEvent(user_id=kyc.user_id, kyc_id=kyc.id))
        return _to_response(kyc)


class ApproveKYCUseCase:
    def __init__(self, kyc_repository: KYCRepository) -> None:
        self._repo = kyc_repository

    async def execute(self, kyc_id: str) -> KYCResponseDTO:
        kyc = await self._repo.get_by_id(kyc_id)
        if not kyc:
            raise NotFoundError("KYCVerification", kyc_id)
        if kyc.status != KYCStatus.SUBMITTED:
            raise InvalidOperationError("KYC must be in SUBMITTED state to approve")

        face_score = kyc.face_similarity_score or 0.0
        final_score = _calculate_trust_score(
            document_submitted=True,
            face_similarity=face_score,
            approved=True,
        )

        # Determine tier from final score
        if final_score >= 85:
            tier = KYCTier.TIER_2
        elif final_score >= 50:
            tier = KYCTier.TIER_1
        else:
            tier = KYCTier.TIER_0

        kyc.approve(tier=tier, trust_score=final_score)
        kyc = await self._repo.update(kyc)

        await event_bus.publish(
            KYCApprovedEvent(
                user_id=kyc.user_id,
                kyc_id=kyc.id,
                tier=kyc.tier.value,
                trust_score=kyc.trust_score,
            )
        )
        await event_bus.publish(
            RiskUpdatedEvent(
                user_id=kyc.user_id,
                trust_score=kyc.trust_score,
                risk_flag=kyc.trust_score < 30,
            )
        )
        return _to_response(kyc)


class RejectKYCUseCase:
    def __init__(self, kyc_repository: KYCRepository) -> None:
        self._repo = kyc_repository

    async def execute(self, kyc_id: str, reason: str) -> KYCResponseDTO:
        kyc = await self._repo.get_by_id(kyc_id)
        if not kyc:
            raise NotFoundError("KYCVerification", kyc_id)
        if kyc.status != KYCStatus.SUBMITTED:
            raise InvalidOperationError("KYC must be in SUBMITTED state to reject")

        kyc.reject(reason=reason)
        kyc = await self._repo.update(kyc)

        await event_bus.publish(
            KYCRejectedEvent(user_id=kyc.user_id, kyc_id=kyc.id, reason=reason)
        )
        return _to_response(kyc)
