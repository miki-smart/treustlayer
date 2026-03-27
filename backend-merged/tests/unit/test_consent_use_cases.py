"""
Unit tests for Consent module use cases.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.modules.consent.application.use_cases.grant_consent import GrantConsentUseCase
from app.modules.consent.application.use_cases.revoke_consent import RevokeConsentUseCase
from app.modules.consent.application.use_cases.list_user_consents import (
    ListUserConsentsUseCase,
)
from app.modules.consent.domain.entities.consent_record import ConsentRecord
from app.modules.identity.domain.entities.user import User, UserRole
from app.core.exceptions import NotFoundError, BadRequestError


class TestGrantConsentUseCase:
    """Test GrantConsentUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "consent_repo": AsyncMock(),
            "user_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return GrantConsentUseCase(
            consent_repo=mock_repos["consent_repo"],
            user_repo=mock_repos["user_repo"],
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
    async def test_grant_consent_new(self, use_case, mock_repos, test_user):
        """Test granting new consent."""
        mock_repos["user_repo"].get_by_id.return_value = test_user
        mock_repos["consent_repo"].get_by_user_and_client.return_value = None
        mock_repos["consent_repo"].create.return_value = ConsentRecord(
            user_id=test_user.id,
            client_id="test-client",
            scopes=["openid", "profile"],
        )
        
        result = await use_case.execute(
            user_id=test_user.id,
            client_id="test-client",
            scopes=["openid", "profile"],
        )
        
        assert result.user_id == test_user.id
        assert result.client_id == "test-client"
        assert "openid" in result.scopes
        mock_repos["consent_repo"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_grant_consent_update_existing(self, use_case, mock_repos, test_user):
        """Test updating existing consent."""
        existing_consent = ConsentRecord(
            user_id=test_user.id,
            client_id="test-client",
            scopes=["openid"],
            is_active=False,
        )
        mock_repos["user_repo"].get_by_id.return_value = test_user
        mock_repos["consent_repo"].get_by_user_and_client.return_value = existing_consent
        mock_repos["consent_repo"].update.return_value = existing_consent
        
        result = await use_case.execute(
            user_id=test_user.id,
            client_id="test-client",
            scopes=["openid", "profile", "email"],
        )
        
        assert result.is_active is True
        assert len(result.scopes) == 3
        mock_repos["consent_repo"].update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_grant_consent_user_not_found(self, use_case, mock_repos):
        """Test granting consent for non-existent user."""
        mock_repos["user_repo"].get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="User not found"):
            await use_case.execute(
                user_id="non-existent",
                client_id="test-client",
                scopes=["openid"],
            )
    
    @pytest.mark.asyncio
    async def test_grant_consent_empty_scopes(self, use_case, mock_repos, test_user):
        """Test granting consent with empty scopes."""
        mock_repos["user_repo"].get_by_id.return_value = test_user
        
        with pytest.raises(BadRequestError, match="At least one scope"):
            await use_case.execute(
                user_id=test_user.id,
                client_id="test-client",
                scopes=[],
            )


class TestRevokeConsentUseCase:
    """Test RevokeConsentUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return RevokeConsentUseCase(consent_repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_revoke_consent_success(self, use_case, mock_repo):
        """Test successful consent revocation."""
        consent = ConsentRecord(
            user_id="user-123",
            client_id="test-client",
            scopes=["openid"],
            is_active=True,
        )
        mock_repo.get_by_user_and_client.return_value = consent
        mock_repo.update.return_value = consent
        
        await use_case.execute(user_id="user-123", client_id="test-client")
        
        assert consent.is_active is False
        assert consent.revoked_at is not None
        mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_consent_not_found(self, use_case, mock_repo):
        """Test revoking non-existent consent."""
        mock_repo.get_by_user_and_client.return_value = None
        
        with pytest.raises(NotFoundError, match="Consent not found"):
            await use_case.execute(user_id="user-123", client_id="test-client")


class TestListUserConsentsUseCase:
    """Test ListUserConsentsUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return ListUserConsentsUseCase(consent_repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_list_consents_success(self, use_case, mock_repo):
        """Test listing user consents."""
        mock_consents = [
            ConsentRecord(
                user_id="user-123",
                client_id=f"client-{i}",
                scopes=["openid"],
            )
            for i in range(3)
        ]
        mock_repo.list_by_user.return_value = mock_consents
        
        result = await use_case.execute(user_id="user-123")
        
        assert len(result) == 3
        assert all(c.user_id == "user-123" for c in result)
        mock_repo.list_by_user.assert_called_once_with("user-123")
