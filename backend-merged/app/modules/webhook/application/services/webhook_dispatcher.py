"""
WebhookDispatcher — dispatch webhook events to subscribers.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.core.security import sign_webhook_payload
from app.modules.webhook.domain.entities.webhook_delivery import (
    DeliveryStatus,
    WebhookDelivery,
)
from app.modules.webhook.domain.repositories.webhook_repository import WebhookRepository

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """
    Webhook event dispatcher.
    
    Sends webhook POST requests with HMAC signatures.
    Handles retries with exponential backoff.
    """
    
    def __init__(self, webhook_repo: WebhookRepository):
        self.webhook_repo = webhook_repo
    
    async def dispatch_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Dispatch event to all subscribers.
        
        Args:
            event_type: Type of event (e.g., "user.kyc.approved")
            payload: Event payload
        """
        subscriptions = await self.webhook_repo.list_subscriptions_by_event(event_type)
        
        if not subscriptions:
            logger.debug(f"No subscriptions for event type: {event_type}")
            return
        
        logger.info(f"Dispatching event {event_type} to {len(subscriptions)} subscribers")
        
        for subscription in subscriptions:
            delivery = WebhookDelivery(
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                target_url=subscription.target_url,
            )
            await self.webhook_repo.create_delivery(delivery)
    
    async def process_delivery(self, delivery: WebhookDelivery, secret: str) -> None:
        """
        Process a single webhook delivery.
        
        Args:
            delivery: Delivery record
            secret: Webhook secret for signing
        """
        import json
        
        payload_bytes = json.dumps(delivery.payload).encode()
        signature = sign_webhook_payload(payload_bytes, secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery-ID": delivery.id,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    delivery.target_url, content=payload_bytes, headers=headers
                )
                
                if 200 <= response.status_code < 300:
                    delivery.mark_success(response.status_code, response.text[:1000])
                    logger.info(
                        f"Webhook delivered successfully: {delivery.id} to {delivery.target_url}"
                    )
                else:
                    self._handle_failure(delivery, f"HTTP {response.status_code}", response.status_code)
        
        except Exception as e:
            self._handle_failure(delivery, str(e))
        
        await self.webhook_repo.update_delivery(delivery)
    
    def _handle_failure(
        self, delivery: WebhookDelivery, error_message: str, response_status: int | None = None
    ) -> None:
        """Handle delivery failure with retry logic."""
        max_retries = settings.WEBHOOK_MAX_RETRIES
        
        if delivery.attempts < max_retries:
            delay_seconds = min(
                settings.WEBHOOK_RETRY_DELAY_SECONDS * (2 ** delivery.attempts),
                settings.WEBHOOK_MAX_DELAY_SECONDS,
            )
            next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            delivery.mark_failed(error_message, response_status, next_retry_at)
            logger.warning(
                f"Webhook delivery failed (attempt {delivery.attempts}/{max_retries}): {delivery.id}, "
                f"retrying in {delay_seconds}s"
            )
        else:
            delivery.mark_failed(error_message, response_status)
            logger.error(
                f"Webhook delivery permanently failed after {max_retries} attempts: {delivery.id}"
            )
