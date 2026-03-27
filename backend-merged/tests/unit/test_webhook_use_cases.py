"""
Unit tests for Webhook module use cases.
"""
import pytest
from unittest.mock import AsyncMock

from app.modules.webhook.application.use_cases.subscribe_webhook import (
    SubscribeWebhookUseCase,
)
from app.modules.webhook.domain.entities.webhook_subscription import WebhookSubscription
from app.modules.app_registry.domain.entities.app import App
from app.core.exceptions import NotFoundError, BadRequestError


class TestSubscribeWebhookUseCase:
    """Test SubscribeWebhookUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "webhook_repo": AsyncMock(),
            "app_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return SubscribeWebhookUseCase(
            webhook_repo=mock_repos["webhook_repo"],
            app_repo=mock_repos["app_repo"],
        )
    
    @pytest.fixture
    def test_app(self):
        """Create test app."""
        return App(
            id="app-123",
            name="Test App",
            owner_id="user-123",
            client_id="test-client",
            allowed_scopes=["openid"],
            redirect_uris=["http://localhost:3000"],
            client_secret_hash="hash",
            api_key_hash="hash",
            is_approved=True,
            is_active=True,
        )
    
    @pytest.mark.asyncio
    async def test_subscribe_webhook_success(self, use_case, mock_repos, test_app):
        """Test successful webhook subscription."""
        mock_repos["app_repo"].get_by_client_id.return_value = test_app
        mock_repos["webhook_repo"].create_subscription.return_value = WebhookSubscription(
            client_id=test_app.client_id,
            event_type="user.kyc.approved",
            target_url="https://example.com/webhook",
            secret="secret-hash",
        )
        
        subscription, webhook_secret = await use_case.execute(
            client_id=test_app.client_id,
            event_type="user.kyc.approved",
            target_url="https://example.com/webhook",
        )
        
        assert subscription.client_id == test_app.client_id
        assert subscription.event_type == "user.kyc.approved"
        assert len(webhook_secret) > 0
        mock_repos["webhook_repo"].create_subscription.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_webhook_client_not_found(self, use_case, mock_repos):
        """Test webhook subscription with non-existent client."""
        mock_repos["app_repo"].get_by_client_id.return_value = None
        
        with pytest.raises(NotFoundError, match="Client not found"):
            await use_case.execute(
                client_id="non-existent",
                event_type="user.created",
                target_url="https://example.com/webhook",
            )
    
    @pytest.mark.asyncio
    async def test_subscribe_webhook_inactive_client(self, use_case, mock_repos, test_app):
        """Test webhook subscription with inactive client."""
        test_app.is_active = False
        mock_repos["app_repo"].get_by_client_id.return_value = test_app
        
        with pytest.raises(BadRequestError, match="not approved or inactive"):
            await use_case.execute(
                client_id=test_app.client_id,
                event_type="user.created",
                target_url="https://example.com/webhook",
            )
    
    @pytest.mark.asyncio
    async def test_subscribe_webhook_invalid_event_type(
        self, use_case, mock_repos, test_app
    ):
        """Test webhook subscription with invalid event type."""
        mock_repos["app_repo"].get_by_client_id.return_value = test_app
        
        with pytest.raises(BadRequestError, match="Invalid event type"):
            await use_case.execute(
                client_id=test_app.client_id,
                event_type="invalid.event",
                target_url="https://example.com/webhook",
            )
    
    @pytest.mark.asyncio
    async def test_subscribe_webhook_invalid_url(self, use_case, mock_repos, test_app):
        """Test webhook subscription with invalid URL."""
        mock_repos["app_repo"].get_by_client_id.return_value = test_app
        
        with pytest.raises(BadRequestError, match="must start with http"):
            await use_case.execute(
                client_id=test_app.client_id,
                event_type="user.created",
                target_url="ftp://example.com/webhook",
            )
