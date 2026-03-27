"""
Unit tests for Trust scoring algorithm.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from app.modules.trust.application.use_cases.calculate_trust_score import (
    CalculateTrustScoreUseCase,
)
from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.identity.domain.entities.user import User, UserRole
from app.modules.kyc.domain.entities.kyc_verification import (
    KYCVerification,
    KYCTier,
    KYCStatus,
)
from app.modules.biometric.domain.entities.biometric_record import (
    BiometricRecord,
    BiometricType,
    BiometricStatus,
)
from app.modules.digital_identity.domain.entities.digital_identity import (
    DigitalIdentity,
    IdentityStatus,
)


class TestCalculateTrustScoreUseCase:
    """Test CalculateTrustScoreUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "trust_repo": AsyncMock(),
            "user_repo": AsyncMock(),
            "kyc_repo": AsyncMock(),
            "biometric_repo": AsyncMock(),
            "identity_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return CalculateTrustScoreUseCase(
            trust_repo=mock_repos["trust_repo"],
            user_repo=mock_repos["user_repo"],
            kyc_repo=mock_repos["kyc_repo"],
            biometric_repo=mock_repos["biometric_repo"],
            identity_repo=mock_repos["identity_repo"],
        )
    
    @pytest.fixture
    def base_user(self):
        """Create base user with no verifications."""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
            is_email_verified=False,
            phone_verified=False,
            created_at=datetime.now(timezone.utc),
        )
    
    @pytest.mark.asyncio
    async def test_trust_score_base_user(self, use_case, mock_repos, base_user):
        """Test trust score for user with no verifications."""
        mock_repos["user_repo"].get_by_id.return_value = base_user
        mock_repos["kyc_repo"].get_by_user_id.return_value = None
        mock_repos["biometric_repo"].list_by_user_and_type.return_value = []
        mock_repos["identity_repo"].get_by_user_id.return_value = None
        mock_repos["trust_repo"].get_by_user_id.return_value = None
        mock_repos["trust_repo"].create.return_value = TrustProfile(
            user_id=base_user.id, trust_score=0.0
        )
        
        result = await use_case.execute(user_id=base_user.id)
        
        assert result.trust_score == 0.0
        assert result.risk_level == "high"
        mock_repos["trust_repo"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trust_score_email_verified(self, use_case, mock_repos, base_user):
        """Test trust score with email verified."""
        base_user.is_email_verified = True
        mock_repos["user_repo"].get_by_id.return_value = base_user
        mock_repos["kyc_repo"].get_by_user_id.return_value = None
        mock_repos["biometric_repo"].list_by_user_and_type.return_value = []
        mock_repos["identity_repo"].get_by_user_id.return_value = None
        mock_repos["trust_repo"].get_by_user_id.return_value = None
        
        profile = TrustProfile(user_id=base_user.id)
        profile.update_score(
            email_verified=True,
            phone_verified=False,
            kyc_tier=0,
            face_verified=False,
            voice_verified=False,
            digital_identity_active=False,
            account_age_days=0,
        )
        mock_repos["trust_repo"].create.return_value = profile
        
        result = await use_case.execute(user_id=base_user.id)
        
        assert result.trust_score >= 20.0
        assert result.email_verified is True
    
    @pytest.mark.asyncio
    async def test_trust_score_full_verification(self, use_case, mock_repos, base_user):
        """Test trust score with all verifications."""
        base_user.is_email_verified = True
        base_user.phone_verified = True
        base_user.created_at = datetime.now(timezone.utc) - timedelta(days=365)
        
        kyc = KYCVerification(
            user_id=base_user.id,
            status=KYCStatus.APPROVED,
            tier=KYCTier.TIER_3,
        )
        
        face_biometric = BiometricRecord(
            user_id=base_user.id,
            type=BiometricType.FACE,
            status=BiometricStatus.VERIFIED,
        )
        
        voice_biometric = BiometricRecord(
            user_id=base_user.id,
            type=BiometricType.VOICE,
            status=BiometricStatus.VERIFIED,
        )
        
        digital_identity = DigitalIdentity(
            user_id=base_user.id,
            identity_id="did:trust:123",
            status=IdentityStatus.ACTIVE,
        )
        
        mock_repos["user_repo"].get_by_id.return_value = base_user
        mock_repos["kyc_repo"].get_by_user_id.return_value = kyc
        mock_repos["biometric_repo"].list_by_user_and_type.side_effect = [
            [face_biometric],
            [voice_biometric],
        ]
        mock_repos["identity_repo"].get_by_user_id.return_value = digital_identity
        mock_repos["trust_repo"].get_by_user_id.return_value = None
        
        profile = TrustProfile(user_id=base_user.id)
        profile.update_score(
            email_verified=True,
            phone_verified=True,
            kyc_tier=3,
            face_verified=True,
            voice_verified=True,
            digital_identity_active=True,
            account_age_days=365,
        )
        mock_repos["trust_repo"].create.return_value = profile
        
        result = await use_case.execute(user_id=base_user.id)
        
        assert result.trust_score >= 90.0
        assert result.risk_level == "low"
        assert result.email_verified is True
        assert result.phone_verified is True
        assert result.kyc_tier == 3
        assert result.face_verified is True
        assert result.voice_verified is True
        assert result.digital_identity_active is True
