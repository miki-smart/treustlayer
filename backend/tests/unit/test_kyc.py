"""
Unit tests for KYC domain logic and use cases.
"""
import pytest
from unittest.mock import AsyncMock

from app.modules.kyc.domain.entities.kyc_verification import (
    KYCStatus,
    KYCTier,
    KYCVerification,
)
from app.modules.kyc.application.use_cases.kyc_use_cases import (
    ApproveKYCUseCase,
    SubmitKYCUseCase,
    _calculate_trust_score,
)
from app.modules.kyc.application.dto.kyc_dto import SubmitKYCDTO
from app.core.exceptions import InvalidOperationError


class TestTrustScoreCalculation:
    def test_zero_score_no_doc(self):
        assert _calculate_trust_score(False, 0.0, False) == 0

    def test_partial_score_doc_submitted(self):
        score = _calculate_trust_score(True, 0.0, False)
        assert score == 30

    def test_face_similarity_bonus(self):
        score = _calculate_trust_score(True, 0.90, False)
        assert score == 50  # 30 + 20

    def test_full_score_approved(self):
        score = _calculate_trust_score(True, 0.90, True)
        assert score == 90  # 30 + 20 + 40

    def test_score_capped_at_100(self):
        score = _calculate_trust_score(True, 0.90, True)
        assert score <= 100


class TestKYCVerificationEntity:
    def test_initial_state(self):
        kyc = KYCVerification(user_id="user-123")
        assert kyc.status == KYCStatus.PENDING
        assert kyc.tier == KYCTier.TIER_0
        assert kyc.trust_score == 0

    def test_submit_changes_status(self):
        kyc = KYCVerification(user_id="user-123")
        kyc.submit("passport", "AB123456", "https://s3/doc.jpg")
        assert kyc.status == KYCStatus.SUBMITTED
        assert kyc.document_type == "passport"

    def test_approve_sets_tier_and_score(self):
        kyc = KYCVerification(user_id="user-123")
        kyc.submit("passport", "AB123456", "https://s3/doc.jpg")
        kyc.approve(tier=KYCTier.TIER_2, trust_score=90)
        assert kyc.status == KYCStatus.APPROVED
        assert kyc.tier == KYCTier.TIER_2
        assert kyc.trust_score == 90
        assert kyc.verified_at is not None

    def test_reject_sets_reason(self):
        kyc = KYCVerification(user_id="user-123")
        kyc.submit("passport", "AB123456", "https://s3/doc.jpg")
        kyc.reject("Document expired")
        assert kyc.status == KYCStatus.REJECTED
        assert kyc.rejection_reason == "Document expired"


class TestSubmitKYCUseCase:
    @pytest.mark.asyncio
    async def test_submit_creates_new_record(self):
        repo = AsyncMock()
        repo.get_by_user_id.return_value = None
        repo.create.side_effect = lambda kyc: kyc

        use_case = SubmitKYCUseCase(repo)
        result = await use_case.execute(
            SubmitKYCDTO(
                user_id="user-1",
                document_type="passport",
                document_number="AB1234",
                document_url="https://s3/doc.jpg",
            )
        )

        assert result.status == KYCStatus.SUBMITTED.value
        repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_to_approved_raises(self):
        from app.modules.kyc.domain.entities.kyc_verification import KYCTier
        approved_kyc = KYCVerification(user_id="user-1")
        approved_kyc.submit("passport", "AB1234", "https://s3/doc.jpg")
        approved_kyc.approve(tier=KYCTier.TIER_2, trust_score=90)

        repo = AsyncMock()
        repo.get_by_user_id.return_value = approved_kyc

        use_case = SubmitKYCUseCase(repo)
        with pytest.raises(InvalidOperationError, match="already approved"):
            await use_case.execute(
                SubmitKYCDTO(
                    user_id="user-1",
                    document_type="passport",
                    document_number="AB1234",
                    document_url="https://s3/doc.jpg",
                )
            )
