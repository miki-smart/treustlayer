"""
WebhookRepository — repository interface for webhook domain.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.webhook.domain.entities.webhook_subscription import WebhookSubscription
from app.modules.webhook.domain.entities.webhook_delivery import WebhookDelivery, DeliveryStatus


class WebhookRepository(ABC):
    """Repository interface for webhook subscriptions and deliveries."""
    
    @abstractmethod
    async def create_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Create new webhook subscription."""
        pass
    
    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID."""
        pass
    
    @abstractmethod
    async def list_subscriptions_by_client(self, client_id: str) -> List[WebhookSubscription]:
        """List subscriptions for a client."""
        pass
    
    @abstractmethod
    async def list_subscriptions_by_event(self, event_type: str) -> List[WebhookSubscription]:
        """List active subscriptions for an event type."""
        pass
    
    @abstractmethod
    async def update_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Update subscription."""
        pass
    
    @abstractmethod
    async def delete_subscription(self, subscription_id: str) -> None:
        """Delete subscription."""
        pass
    
    @abstractmethod
    async def create_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Create new delivery record."""
        pass
    
    @abstractmethod
    async def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID."""
        pass
    
    @abstractmethod
    async def list_deliveries_by_subscription(
        self, subscription_id: str, skip: int = 0, limit: int = 50
    ) -> List[WebhookDelivery]:
        """List deliveries for a subscription."""
        pass
    
    @abstractmethod
    async def list_pending_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """List pending/retrying deliveries for worker."""
        pass
    
    @abstractmethod
    async def update_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Update delivery record."""
        pass
