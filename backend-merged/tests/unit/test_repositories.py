"""
Unit tests for repository implementations.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.persistence.auth_repository_impl import (
    SQLAlchemyAuthRepository,
)
from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.entities.refresh_token import RefreshToken


class TestSQLAlchemyAuthRepository:
    """Test SQLAlchemyAuthRepository."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def auth_repo(self, mock_session):
        """Create auth repository instance."""
        return SQLAlchemyAuthRepository(session=mock_session)
    
    @pytest.mark.asyncio
    async def test_save_authorization_code(self, auth_repo, mock_session):
        """Test saving authorization code."""
        code = AuthorizationCode(
            client_id="client-123",
            user_id="user-123",
            redirect_uri="http://localhost:3000",
            scopes=["openid"],
        )
        
        result = await auth_repo.save_authorization_code(code)
        
        assert result.client_id == code.client_id
        assert result.user_id == code.user_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_refresh_token(self, auth_repo, mock_session):
        """Test saving refresh token."""
        token = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        result = await auth_repo.save_refresh_token(token)
        
        assert result.user_id == token.user_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_code_as_used(self, auth_repo, mock_session):
        """Test marking authorization code as used."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(is_used=False)
        mock_session.execute.return_value = mock_result
        
        await auth_repo.mark_code_as_used("code-123")
        
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_all_refresh_tokens(self, auth_repo, mock_session):
        """Test revoking all user refresh tokens."""
        await auth_repo.revoke_all_refresh_tokens("user-123")
        
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()


class TestConsentRepository:
    """Test consent repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_create_consent(self, mock_session):
        """Test creating consent record."""
        from app.modules.consent.infrastructure.persistence.consent_repository_impl import (
            SQLAlchemyConsentRepository,
        )
        from app.modules.consent.domain.entities.consent_record import ConsentRecord
        
        repo = SQLAlchemyConsentRepository(session=mock_session)
        
        consent = ConsentRecord(
            user_id="user-123",
            client_id="client-123",
            scopes=["openid", "profile"],
        )
        
        result = await repo.create(consent)
        
        assert result.user_id == consent.user_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_by_user(self, mock_session):
        """Test listing consents by user."""
        from app.modules.consent.infrastructure.persistence.consent_repository_impl import (
            SQLAlchemyConsentRepository,
        )
        
        repo = SQLAlchemyConsentRepository(session=mock_session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await repo.list_by_user("user-123")
        
        assert isinstance(result, list)
        mock_session.execute.assert_called_once()


class TestAppRepository:
    """Test app repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_create_app(self, mock_session):
        """Test creating app."""
        from app.modules.app_registry.infrastructure.persistence.app_repository_impl import (
            SQLAlchemyAppRepository,
        )
        from app.modules.app_registry.domain.entities.app import App
        
        repo = SQLAlchemyAppRepository(session=mock_session)
        
        app = App(
            name="Test App",
            owner_id="user-123",
            allowed_scopes=["openid"],
            redirect_uris=["http://localhost:3000"],
        )
        
        result = await repo.create(app)
        
        assert result.name == app.name
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_by_owner(self, mock_session):
        """Test listing apps by owner."""
        from app.modules.app_registry.infrastructure.persistence.app_repository_impl import (
            SQLAlchemyAppRepository,
        )
        
        repo = SQLAlchemyAppRepository(session=mock_session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await repo.list_by_owner("user-123")
        
        assert isinstance(result, list)
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_public_apps(self, mock_session):
        """Test listing public marketplace apps."""
        from app.modules.app_registry.infrastructure.persistence.app_repository_impl import (
            SQLAlchemyAppRepository,
        )
        
        repo = SQLAlchemyAppRepository(session=mock_session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await repo.list_public(skip=0, limit=50)
        
        assert isinstance(result, list)
        mock_session.execute.assert_called_once()


class TestWebhookRepository:
    """Test webhook repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_create_subscription(self, mock_session):
        """Test creating webhook subscription."""
        from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import (
            SQLAlchemyWebhookRepository,
        )
        from app.modules.webhook.domain.entities.webhook_subscription import (
            WebhookSubscription,
        )
        
        repo = SQLAlchemyWebhookRepository(session=mock_session)
        
        subscription = WebhookSubscription(
            client_id="client-123",
            event_type="user.created",
            target_url="https://example.com/webhook",
            secret="secret-hash",
        )
        
        result = await repo.create_subscription(subscription)
        
        assert result.client_id == subscription.client_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_delivery(self, mock_session):
        """Test creating webhook delivery."""
        from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import (
            SQLAlchemyWebhookRepository,
        )
        from app.modules.webhook.domain.entities.webhook_delivery import (
            WebhookDelivery,
        )
        
        repo = SQLAlchemyWebhookRepository(session=mock_session)
        
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={"user_id": "user-123"},
            target_url="https://example.com/webhook",
        )
        
        result = await repo.create_delivery(delivery)
        
        assert result.subscription_id == delivery.subscription_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestAuditRepository:
    """Test audit repository operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_create_audit_entry(self, mock_session):
        """Test creating audit entry."""
        from app.modules.audit.infrastructure.persistence.audit_repository_impl import (
            SQLAlchemyAuditRepository,
        )
        from app.modules.audit.domain.entities.audit_entry import AuditEntry
        
        repo = SQLAlchemyAuditRepository(session=mock_session)
        
        entry = AuditEntry(
            action="user.created",
            resource_type="user",
            actor_id="admin-123",
            resource_id="user-456",
        )
        
        result = await repo.create(entry)
        
        assert result.action == entry.action
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_entries_with_filters(self, mock_session):
        """Test listing audit entries with filters."""
        from app.modules.audit.infrastructure.persistence.audit_repository_impl import (
            SQLAlchemyAuditRepository,
        )
        
        repo = SQLAlchemyAuditRepository(session=mock_session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        result = await repo.list_entries(
            action="user.created",
            resource_type="user",
            actor_id="admin-123",
            skip=0,
            limit=50,
        )
        
        assert isinstance(result, list)
        mock_session.execute.assert_called_once()
