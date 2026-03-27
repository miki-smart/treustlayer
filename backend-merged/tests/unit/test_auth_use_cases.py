"""
Unit tests for Auth module use cases.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from app.modules.auth.application.use_cases.authorize import AuthorizeUseCase
from app.modules.auth.application.use_cases.exchange_token import ExchangeTokenUseCase
from app.modules.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.entities.user import User, UserRole
from app.modules.kyc.domain.entities.kyc_verification import KYCVerification, KYCTier, KYCStatus
from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.core.exceptions import UnauthorizedError, BadRequestError


class TestAuthorizeUseCase:
    """Test AuthorizeUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "auth_repo": AsyncMock(),
            "user_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return AuthorizeUseCase(
            auth_repo=mock_repos["auth_repo"],
            user_repo=mock_repos["user_repo"],
        )
    
    @pytest.fixture
    def test_user(self):
        """Create test user."""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2J8T5LZoYe",  # "password123"
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True,
        )
    
    @pytest.mark.asyncio
    async def test_authorize_success(self, use_case, mock_repos, test_user):
        """Test successful authorization."""
        mock_repos["user_repo"].get_by_email.return_value = test_user
        mock_repos["auth_repo"].save_authorization_code.return_value = AuthorizationCode(
            client_id="test-client",
            user_id=test_user.id,
            redirect_uri="http://localhost:3000/callback",
            scopes=["openid", "profile"],
        )
        
        result = await use_case.execute(
            email="test@example.com",
            password="password123",
            client_id="test-client",
            redirect_uri="http://localhost:3000/callback",
            scopes=["openid", "profile"],
        )
        
        assert result.user_id == test_user.id
        assert result.client_id == "test-client"
        assert "openid" in result.scopes
        mock_repos["auth_repo"].save_authorization_code.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authorize_invalid_credentials(self, use_case, mock_repos):
        """Test authorization with invalid credentials."""
        mock_repos["user_repo"].get_by_email.return_value = None
        
        with pytest.raises(UnauthorizedError, match="Invalid credentials"):
            await use_case.execute(
                email="wrong@example.com",
                password="wrongpass",
                client_id="test-client",
                redirect_uri="http://localhost:3000/callback",
                scopes=["openid"],
            )
    
    @pytest.mark.asyncio
    async def test_authorize_inactive_user(self, use_case, mock_repos, test_user):
        """Test authorization with inactive user."""
        test_user.is_active = False
        mock_repos["user_repo"].get_by_email.return_value = test_user
        
        with pytest.raises(UnauthorizedError, match="deactivated"):
            await use_case.execute(
                email="test@example.com",
                password="password123",
                client_id="test-client",
                redirect_uri="http://localhost:3000/callback",
                scopes=["openid"],
            )
    
    @pytest.mark.asyncio
    async def test_authorize_missing_openid_scope(self, use_case, mock_repos, test_user):
        """Test authorization without openid scope."""
        mock_repos["user_repo"].get_by_email.return_value = test_user
        
        with pytest.raises(BadRequestError, match="openid.*required"):
            await use_case.execute(
                email="test@example.com",
                password="password123",
                client_id="test-client",
                redirect_uri="http://localhost:3000/callback",
                scopes=["profile"],  # Missing openid
            )


class TestExchangeTokenUseCase:
    """Test ExchangeTokenUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "auth_repo": AsyncMock(),
            "user_repo": AsyncMock(),
            "kyc_repo": AsyncMock(),
            "trust_repo": AsyncMock(),
            "biometric_repo": AsyncMock(),
            "identity_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return ExchangeTokenUseCase(
            auth_repo=mock_repos["auth_repo"],
            user_repo=mock_repos["user_repo"],
            kyc_repo=mock_repos["kyc_repo"],
            trust_repo=mock_repos["trust_repo"],
            biometric_repo=mock_repos["biometric_repo"],
            identity_repo=mock_repos["identity_repo"],
        )
    
    @pytest.fixture
    def test_auth_code(self):
        """Create test authorization code."""
        return AuthorizationCode(
            code="test-code-123",
            client_id="test-client",
            user_id="user-123",
            redirect_uri="http://localhost:3000/callback",
            scopes=["openid", "profile", "email"],
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            is_used=False,
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
            is_email_verified=True,
        )
    
    @pytest.mark.asyncio
    async def test_exchange_token_success(
        self, use_case, mock_repos, test_auth_code, test_user
    ):
        """Test successful token exchange."""
        mock_repos["auth_repo"].get_authorization_code.return_value = test_auth_code
        mock_repos["user_repo"].get_by_id.return_value = test_user
        mock_repos["kyc_repo"].get_by_user_id.return_value = None
        mock_repos["trust_repo"].get_by_user_id.return_value = None
        mock_repos["biometric_repo"].list_by_user_and_type.return_value = []
        mock_repos["identity_repo"].get_by_user_id.return_value = None
        mock_repos["auth_repo"].save_refresh_token.return_value = RefreshToken(
            user_id=test_user.id,
            client_id="test-client",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        result = await use_case.execute(
            code="test-code-123",
            client_id="test-client",
            client_secret="secret",
            redirect_uri="http://localhost:3000/callback",
        )
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert "id_token" in result
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 900
        mock_repos["auth_repo"].mark_code_as_used.assert_called_once_with("test-code-123")
    
    @pytest.mark.asyncio
    async def test_exchange_token_expired_code(self, use_case, mock_repos, test_auth_code):
        """Test token exchange with expired code."""
        test_auth_code.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        mock_repos["auth_repo"].get_authorization_code.return_value = test_auth_code
        
        with pytest.raises(UnauthorizedError, match="expired"):
            await use_case.execute(
                code="test-code-123",
                client_id="test-client",
                client_secret="secret",
                redirect_uri="http://localhost:3000/callback",
            )
    
    @pytest.mark.asyncio
    async def test_exchange_token_used_code(self, use_case, mock_repos, test_auth_code):
        """Test token exchange with already used code."""
        test_auth_code.is_used = True
        mock_repos["auth_repo"].get_authorization_code.return_value = test_auth_code
        
        with pytest.raises(UnauthorizedError, match="already used"):
            await use_case.execute(
                code="test-code-123",
                client_id="test-client",
                client_secret="secret",
                redirect_uri="http://localhost:3000/callback",
            )
    
    @pytest.mark.asyncio
    async def test_exchange_token_client_mismatch(self, use_case, mock_repos, test_auth_code):
        """Test token exchange with mismatched client_id."""
        mock_repos["auth_repo"].get_authorization_code.return_value = test_auth_code
        
        with pytest.raises(UnauthorizedError, match="Client ID mismatch"):
            await use_case.execute(
                code="test-code-123",
                client_id="wrong-client",
                client_secret="secret",
                redirect_uri="http://localhost:3000/callback",
            )


class TestRefreshTokenUseCase:
    """Test RefreshTokenUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "auth_repo": AsyncMock(),
            "user_repo": AsyncMock(),
            "kyc_repo": AsyncMock(),
            "trust_repo": AsyncMock(),
            "biometric_repo": AsyncMock(),
            "identity_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return RefreshTokenUseCase(
            auth_repo=mock_repos["auth_repo"],
            user_repo=mock_repos["user_repo"],
            kyc_repo=mock_repos["kyc_repo"],
            trust_repo=mock_repos["trust_repo"],
            biometric_repo=mock_repos["biometric_repo"],
            identity_repo=mock_repos["identity_repo"],
        )
    
    @pytest.fixture
    def test_refresh_token(self):
        """Create test refresh token."""
        return RefreshToken(
            id="token-123",
            user_id="user-123",
            client_id="test-client",
            token_hash="hash123",
            scopes=["openid", "profile"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
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
            is_email_verified=True,
        )
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, use_case, mock_repos, test_refresh_token, test_user
    ):
        """Test successful token refresh."""
        mock_repos["auth_repo"].get_refresh_token.return_value = test_refresh_token
        mock_repos["user_repo"].get_by_id.return_value = test_user
        mock_repos["kyc_repo"].get_by_user_id.return_value = None
        mock_repos["trust_repo"].get_by_user_id.return_value = None
        mock_repos["biometric_repo"].list_by_user_and_type.return_value = []
        mock_repos["identity_repo"].get_by_user_id.return_value = None
        
        result = await use_case.execute(
            refresh_token_value="token-value",
            client_id="test-client",
            client_secret="secret",
        )
        
        assert "access_token" in result
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 900
        mock_repos["auth_repo"].save_refresh_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, use_case, mock_repos, test_refresh_token):
        """Test refresh with expired token."""
        test_refresh_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_repos["auth_repo"].get_refresh_token.return_value = test_refresh_token
        
        with pytest.raises(UnauthorizedError, match="expired or revoked"):
            await use_case.execute(
                refresh_token_value="token-value",
                client_id="test-client",
                client_secret="secret",
            )
    
    @pytest.mark.asyncio
    async def test_refresh_token_revoked(self, use_case, mock_repos, test_refresh_token):
        """Test refresh with revoked token."""
        test_refresh_token.is_revoked = True
        mock_repos["auth_repo"].get_refresh_token.return_value = test_refresh_token
        
        with pytest.raises(UnauthorizedError, match="expired or revoked"):
            await use_case.execute(
                refresh_token_value="token-value",
                client_id="test-client",
                client_secret="secret",
            )
    
    @pytest.mark.asyncio
    async def test_refresh_token_client_mismatch(
        self, use_case, mock_repos, test_refresh_token
    ):
        """Test refresh with mismatched client_id."""
        mock_repos["auth_repo"].get_refresh_token.return_value = test_refresh_token
        
        with pytest.raises(UnauthorizedError, match="Client ID mismatch"):
            await use_case.execute(
                refresh_token_value="token-value",
                client_id="wrong-client",
                client_secret="secret",
            )
