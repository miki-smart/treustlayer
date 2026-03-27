"""
WebhookSubscription — webhook event subscription.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class WebhookSubscription:
    """
    Webhook event subscription.
    
    Attributes:
        client_id: OAuth2 client that subscribed
        event_type: Type of event to subscribe to
        target_url: URL to send webhook POST requests
        secret: Webhook secret for HMAC signature
        is_active: Whether subscription is active
    """
    client_id: str
    event_type: str
    target_url: str
    secret: str
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def deactivate(self) -> None:
        """Deactivate subscription."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
