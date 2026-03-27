"""
Webhook domain entities — no framework imports.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"  # exceeded max_attempts


@dataclass
class WebhookSubscription:
    client_id: str
    event_type: str
    target_url: str
    secret: str  # HMAC-SHA256 signing secret
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WebhookDelivery:
    client_id: str
    event_type: str
    payload: Dict[str, Any]
    target_url: str
    max_attempts: int = 3
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    next_retry_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    response_code: Optional[int] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def mark_delivered(self, response_code: int) -> None:
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.now(timezone.utc)
        self.response_code = response_code
        self.attempts += 1

    def mark_failed(self, retry_after_seconds: int = 60) -> None:
        from datetime import timedelta
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            self.status = DeliveryStatus.DEAD
            self.next_retry_at = None
        else:
            self.status = DeliveryStatus.FAILED
            self.next_retry_at = datetime.now(timezone.utc) + timedelta(
                seconds=retry_after_seconds * (2 ** self.attempts)
            )

    def is_retryable(self) -> bool:
        return self.status == DeliveryStatus.FAILED and self.next_retry_at is not None
