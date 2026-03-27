"""
SubscribeWebhookUseCase — subscribe to webhook events.
"""
import logging

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import generate_secure_token, hash_secret
from app.modules.app_registry.domain.repositories.app_repository import AppRepository
from app.modules.webhook.domain.entities.webhook_subscription import WebhookSubscription
from app.modules.webhook.domain.repositories.webhook_repository import WebhookRepository

logger = logging.getLogger(__name__)


class SubscribeWebhookUseCase:
    """
    Subscribe to webhook events.
    
    Generates webhook secret for HMAC signature verification.
    """
    
    def __init__(self, webhook_repo: WebhookRepository, app_repo: AppRepository):
        self.webhook_repo = webhook_repo
        self.app_repo = app_repo
    
    async def execute(
        self, client_id: str, event_type: str, target_url: str
    ) -> tuple[WebhookSubscription, str]:
        """
        Subscribe to webhook events.
        
        Args:
            client_id: OAuth2 client ID
            event_type: Event type to subscribe to
            target_url: URL to send webhooks to
        
        Returns:
            Tuple of (subscription, webhook_secret)
        
        Raises:
            NotFoundError: Client not found
            BadRequestError: Invalid input
        """
        # Validate client exists
        app = await self.app_repo.get_by_client_id(client_id)
        if not app:
            raise NotFoundError("Client not found")
        
        if not app.is_approved or not app.is_active:
            raise BadRequestError("Client not approved or inactive")
        
        # Validate event type
        valid_events = {
            "user.created",
            "user.updated",
            "user.kyc.submitted",
            "user.kyc.approved",
            "user.kyc.rejected",
            "user.biometric.verified",
            "user.identity.created",
            "user.trust_score.updated",
        }
        if event_type not in valid_events:
            raise BadRequestError(f"Invalid event type. Valid types: {valid_events}")
        
        # Validate target URL
        if not target_url.startswith(("http://", "https://")):
            raise BadRequestError("Target URL must start with http:// or https://")
        
        # Generate webhook secret
        webhook_secret = generate_secure_token(32)
        secret_hash = hash_secret(webhook_secret)
        
        # Create subscription
        subscription = WebhookSubscription(
            client_id=client_id,
            event_type=event_type,
            target_url=target_url,
            secret=secret_hash,
        )
        
        saved = await self.webhook_repo.create_subscription(subscription)
        
        logger.info(f"Webhook subscription created: {saved.id} for event {event_type}")
        
        return saved, webhook_secret
