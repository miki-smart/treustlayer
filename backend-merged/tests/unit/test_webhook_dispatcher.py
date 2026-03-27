"""
Unit tests for Webhook Dispatcher service.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.modules.webhook.application.services.webhook_dispatcher import (
    WebhookDispatcher,
)
from app.modules.webhook.domain.entities.webhook_subscription import WebhookSubscription
from app.modules.webhook.domain.entities.webhook_delivery import (
    WebhookDelivery,
    DeliveryStatus,
)


class TestWebhookDispatcher:
    """Test WebhookDispatcher service."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def dispatcher(self, mock_repo):
        """Create dispatcher instance."""
        return WebhookDispatcher(webhook_repo=mock_repo)
    
    @pytest.fixture
    def test_subscription(self):
        """Create test subscription."""
        return WebhookSubscription(
            id="sub-123",
            client_id="client-123",
            event_type="user.created",
            target_url="https://example.com/webhook",
            secret="secret-hash",
        )
    
    @pytest.mark.asyncio
    async def test_dispatch_event_creates_deliveries(
        self, dispatcher, mock_repo, test_subscription
    ):
        """Test that dispatching event creates delivery records."""
        mock_repo.list_subscriptions_by_event.return_value = [test_subscription]
        mock_repo.create_delivery.return_value = WebhookDelivery(
            subscription_id=test_subscription.id,
            event_type="user.created",
            payload={"user_id": "user-123"},
            target_url=test_subscription.target_url,
        )
        
        await dispatcher.dispatch_event(
            event_type="user.created",
            payload={"user_id": "user-123"},
        )
        
        mock_repo.list_subscriptions_by_event.assert_called_once_with("user.created")
        mock_repo.create_delivery.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dispatch_event_no_subscribers(self, dispatcher, mock_repo):
        """Test dispatching event with no subscribers."""
        mock_repo.list_subscriptions_by_event.return_value = []
        
        await dispatcher.dispatch_event(
            event_type="user.created",
            payload={"user_id": "user-123"},
        )
        
        mock_repo.create_delivery.assert_not_called()
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_process_delivery_success(
        self, mock_client_class, dispatcher, mock_repo
    ):
        """Test successful webhook delivery."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={"user_id": "user-123"},
            target_url="https://example.com/webhook",
        )
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        await dispatcher.process_delivery(delivery, secret="webhook-secret")
        
        assert delivery.status == DeliveryStatus.SUCCESS
        assert delivery.attempts == 1
        assert delivery.response_status == 200
        mock_repo.update_delivery.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_process_delivery_failure_with_retry(
        self, mock_client_class, dispatcher, mock_repo
    ):
        """Test failed webhook delivery with retry."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={"user_id": "user-123"},
            target_url="https://example.com/webhook",
        )
        
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        await dispatcher.process_delivery(delivery, secret="webhook-secret")
        
        assert delivery.status == DeliveryStatus.RETRYING
        assert delivery.attempts == 1
        assert delivery.next_retry_at is not None
        mock_repo.update_delivery.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_process_delivery_max_retries_exceeded(
        self, mock_client_class, dispatcher, mock_repo
    ):
        """Test delivery failure after max retries."""
        delivery = WebhookDelivery(
            subscription_id="sub-123",
            event_type="user.created",
            payload={"user_id": "user-123"},
            target_url="https://example.com/webhook",
            attempts=5,  # Already at max retries
        )
        
        mock_response = AsyncMock()
        mock_response.status_code = 500
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        await dispatcher.process_delivery(delivery, secret="webhook-secret")
        
        assert delivery.status == DeliveryStatus.FAILED
        assert delivery.next_retry_at is None


class TestPKCE:
    """Test PKCE verification."""
    
    def test_verify_pkce_s256_success(self):
        """Test PKCE S256 verification success."""
        import base64
        import hashlib
        
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        
        assert verify_pkce(verifier, challenge, "S256") is True
    
    def test_verify_pkce_s256_failure(self):
        """Test PKCE S256 verification failure."""
        import base64
        import hashlib
        
        verifier = "correct_verifier"
        wrong_verifier = "wrong_verifier"
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )
        
        assert verify_pkce(wrong_verifier, challenge, "S256") is False
    
    def test_verify_pkce_plain_success(self):
        """Test PKCE plain verification success."""
        verifier = "test_verifier"
        challenge = verifier
        
        assert verify_pkce(verifier, challenge, "plain") is True
    
    def test_verify_pkce_plain_failure(self):
        """Test PKCE plain verification failure."""
        assert verify_pkce("wrong", "challenge", "plain") is False


class TestWebhookSigning:
    """Test webhook payload signing."""
    
    def test_sign_webhook_payload(self):
        """Test webhook payload signing."""
        payload = b'{"event": "user.created"}'
        secret = "webhook_secret"
        
        signature = sign_webhook_payload(payload, secret)
        
        assert signature.startswith("sha256=")
        assert len(signature) > 7
    
    def test_sign_webhook_payload_consistency(self):
        """Test that signing is consistent."""
        payload = b'{"event": "test"}'
        secret = "secret"
        
        sig1 = sign_webhook_payload(payload, secret)
        sig2 = sign_webhook_payload(payload, secret)
        
        assert sig1 == sig2
    
    def test_sign_webhook_payload_different_payloads(self):
        """Test that different payloads produce different signatures."""
        secret = "secret"
        
        sig1 = sign_webhook_payload(b'{"event": "test1"}', secret)
        sig2 = sign_webhook_payload(b'{"event": "test2"}', secret)
        
        assert sig1 != sig2
