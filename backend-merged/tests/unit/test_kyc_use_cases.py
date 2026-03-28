"""
Unit tests for KYC module use cases.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.modules.kyc.application.use_cases.submit_kyc import SubmitKYCUseCase
from app.modules.kyc.application.use_cases.approve_kyc import ApproveKYCUseCase
from app.modules.kyc.application.use_cases.reject_kyc import RejectKYCUseCase
from app.modules.kyc.application.use_cases.list_kyc_queue import ListKYCQueueUseCase
from app.modules.kyc.domain.entities.kyc_verification import (
    KYCVerification,
    KYCStatus,
    KYCTier,
)
from app.modules.identity.domain.entities.user import User, UserRole
from app.core.exceptions import NotFoundError, BadRequestError


class TestSubmitKYCUseCase:
    """Test SubmitKYCUseCase."""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        return {
            "kyc_repo": AsyncMock(),
            "user_repo": AsyncMock(),
            "file_storage": AsyncMock(),
            "ocr_service": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_deps):
        """Create use case instance."""
        return SubmitKYCUseCase(
            kyc_repo=mock_deps["kyc_repo"],
            user_repo=mock_deps["user_repo"],
            file_storage=mock_deps["file_storage"],
            ocr_service=mock_deps["ocr_service"],
        )
    
    @pytest.fixture
    def test_user(self):
        """Create test user."""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
    
    @pytest.mark.asyncio
    async def test_submit_kyc_success(self, use_case, mock_deps, test_user):
        """Test successful KYC submission."""
        mock_deps["user_repo"].get_by_id.return_value = test_user
        mock_deps["kyc_repo"].get_by_user_id.return_value = None
        mock_deps["file_storage"].save_file.side_effect = [
            "uploads/kyc/user-123/id_front.jpg",
            "uploads/kyc/user-123/utility_bill.jpg",
            "uploads/kyc/user-123/face_image.jpg",
        ]
        mock_deps["ocr_service"].extract_id_front = AsyncMock(
            return_value={
                "success": True,
                "extracted": {
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-01",
                    "document_type": "passport",
                    "document_number": "AB123456",
                },
                "confidence": 0.95,
            }
        )
        mock_deps["ocr_service"].extract_id_back = AsyncMock(
            return_value={"success": True, "extracted": {}, "confidence": 0.0}
        )
        mock_deps["ocr_service"].extract_utility_bill = AsyncMock(
            return_value={
                "success": True,
                "extracted": {
                    "address": "123 Main St",
                    "billing_name": "John Doe",
                },
                "confidence": 0.90,
            }
        )
        mock_deps["kyc_repo"].create.return_value = KYCVerification(
            user_id=test_user.id,
            status=KYCStatus.PENDING,
        )
        
        result = await use_case.execute(
            user_id=test_user.id,
            id_front_bytes=b"fake-image-data",
            id_back_bytes=None,
            utility_bill_bytes=b"fake-bill-data",
            face_image_bytes=b"fake-face-data",
        )
        
        assert result.user_id == test_user.id
        assert result.status == KYCStatus.PENDING
        mock_deps["kyc_repo"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_kyc_user_not_found(self, use_case, mock_deps):
        """Test KYC submission with non-existent user."""
        mock_deps["user_repo"].get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="User not found"):
            await use_case.execute(
                user_id="non-existent",
                id_front_bytes=b"data",
                id_back_bytes=None,
                utility_bill_bytes=b"data",
                face_image_bytes=b"data",
            )
    
    @pytest.mark.asyncio
    async def test_submit_kyc_already_approved(self, use_case, mock_deps, test_user):
        """Test KYC submission when already approved."""
        mock_deps["user_repo"].get_by_id.return_value = test_user
        mock_deps["kyc_repo"].get_by_user_id.return_value = KYCVerification(
            user_id=test_user.id,
            status=KYCStatus.APPROVED,
        )
        
        with pytest.raises(BadRequestError, match="already approved"):
            await use_case.execute(
                user_id=test_user.id,
                id_front_bytes=b"data",
                id_back_bytes=None,
                utility_bill_bytes=b"data",
                face_image_bytes=b"data",
            )


class TestApproveKYCUseCase:
    """Test ApproveKYCUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return ApproveKYCUseCase(kyc_repo=mock_repo)
    
    @pytest.fixture
    def test_kyc(self):
        """Create test KYC verification."""
        return KYCVerification(
            id="kyc-123",
            user_id="user-123",
            status=KYCStatus.PENDING,
            tier=KYCTier.TIER_0,
        )
    
    @pytest.mark.asyncio
    async def test_approve_kyc_success(self, use_case, mock_repo, test_kyc):
        """Test successful KYC approval."""
        mock_repo.get_by_id.return_value = test_kyc
        mock_repo.update.return_value = test_kyc
        
        result = await use_case.execute(
            verification_id="kyc-123",
            reviewer_id="admin-123",
            tier=KYCTier.TIER_2,
            notes="Approved",
        )
        
        assert result.status == KYCStatus.APPROVED
        assert result.tier == KYCTier.TIER_2
        assert result.reviewer_id == "admin-123"
        mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_kyc_not_found(self, use_case, mock_repo):
        """Test approval of non-existent KYC."""
        mock_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="not found"):
            await use_case.execute(
                verification_id="non-existent",
                reviewer_id="admin-123",
                tier=KYCTier.TIER_1,
            )
    
    @pytest.mark.asyncio
    async def test_approve_kyc_already_approved(self, use_case, mock_repo, test_kyc):
        """Test approval of already approved KYC."""
        test_kyc.status = KYCStatus.APPROVED
        mock_repo.get_by_id.return_value = test_kyc
        
        with pytest.raises(BadRequestError, match="already approved"):
            await use_case.execute(
                verification_id="kyc-123",
                reviewer_id="admin-123",
                tier=KYCTier.TIER_1,
            )


class TestRejectKYCUseCase:
    """Test RejectKYCUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return RejectKYCUseCase(kyc_repo=mock_repo)
    
    @pytest.fixture
    def test_kyc(self):
        """Create test KYC verification."""
        return KYCVerification(
            id="kyc-123",
            user_id="user-123",
            status=KYCStatus.PENDING,
        )
    
    @pytest.mark.asyncio
    async def test_reject_kyc_success(self, use_case, mock_repo, test_kyc):
        """Test successful KYC rejection."""
        mock_repo.get_by_id.return_value = test_kyc
        mock_repo.update.return_value = test_kyc
        
        result = await use_case.execute(
            verification_id="kyc-123",
            reviewer_id="admin-123",
            reason="Documents unclear",
        )
        
        assert result.status == KYCStatus.REJECTED
        assert result.rejection_reason == "Documents unclear"
        assert result.reviewer_id == "admin-123"
        mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reject_approved_kyc(self, use_case, mock_repo, test_kyc):
        """Test rejection of approved KYC."""
        test_kyc.status = KYCStatus.APPROVED
        mock_repo.get_by_id.return_value = test_kyc
        
        with pytest.raises(BadRequestError, match="Cannot reject approved"):
            await use_case.execute(
                verification_id="kyc-123",
                reviewer_id="admin-123",
                reason="Test",
            )


class TestListKYCQueueUseCase:
    """Test ListKYCQueueUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return ListKYCQueueUseCase(kyc_repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_list_queue_success(self, use_case, mock_repo):
        """Test listing KYC queue."""
        mock_verifications = [
            KYCVerification(user_id=f"user-{i}", status=KYCStatus.PENDING)
            for i in range(3)
        ]
        mock_repo.list_by_status.return_value = mock_verifications
        
        result = await use_case.execute(KYCStatus.PENDING, skip=0, limit=50)
        
        assert len(result) == 3
        assert all(v.status == KYCStatus.PENDING for v in result)
        mock_repo.list_by_status.assert_called_once_with(KYCStatus.PENDING, 0, 50)
