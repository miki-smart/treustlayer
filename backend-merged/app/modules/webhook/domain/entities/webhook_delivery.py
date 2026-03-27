"""
WebhookDelivery — webhook delivery attempt record.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookDelivery:
    """
    Webhook delivery attempt.
    
    Attributes:
        subscription_id: Subscription that triggered this delivery
        event_type: Type of event
        payload: Event payload (JSON)
        target_url: Target URL
        status: Delivery status
        attempts: Number of delivery attempts
        last_attempt_at: Timestamp of last attempt
        next_retry_at: Timestamp of next retry
        response_status: HTTP response status code
        response_body: HTTP response body
        error_message: Error message if failed
    """
    subscription_id: str
    event_type: str
    payload: dict
    target_url: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def mark_success(self, response_status: int, response_body: str) -> None:
        """Mark delivery as successful."""
        self.status = DeliveryStatus.SUCCESS
        self.response_status = response_status
        self.response_body = response_body
        self.last_attempt_at = datetime.now(timezone.utc)
        self.attempts += 1
    
    def mark_failed(
        self, error_message: str, response_status: Optional[int] = None, next_retry_at: Optional[datetime] = None
    ) -> None:
        """Mark delivery as failed."""
        self.status = DeliveryStatus.FAILED if not next_retry_at else DeliveryStatus.RETRYING
        self.error_message = error_message
        self.response_status = response_status
        self.last_attempt_at = datetime.now(timezone.utc)
        self.next_retry_at = next_retry_at
        self.attempts += 1
