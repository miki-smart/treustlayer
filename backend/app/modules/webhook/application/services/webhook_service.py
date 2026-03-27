"""
WebhookService — listens to domain events and dispatches outbound webhooks.

Responsibilities:
  1. For each domain event, look up active subscriptions.
  2. Create WebhookDelivery records (queued for dispatch).
  3. WebhookWorker (background task) processes the queue.
"""
import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.core.security import sign_webhook_payload
from app.modules.webhook.domain.entities.webhook_entities import WebhookDelivery, WebhookSubscription
from app.modules.webhook.domain.repositories.webhook_repositories import (
    WebhookDeliveryRepository,
    WebhookSubscriptionRepository,
)

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(
        self,
        subscription_repository: WebhookSubscriptionRepository,
        delivery_repository: WebhookDeliveryRepository,
    ) -> None:
        self._subs = subscription_repository
        self._deliveries = delivery_repository

    async def dispatch_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """Queue deliveries for all subscribers of this event_type."""
        subs = await self._subs.get_by_event_type(event_type)
        for sub in subs:
            delivery = WebhookDelivery(
                client_id=sub.client_id,
                event_type=event_type,
                payload=payload,
                target_url=sub.target_url,
                max_attempts=settings.WEBHOOK_MAX_RETRIES,
            )
            await self._deliveries.create(delivery)

    async def process_delivery(self, delivery: WebhookDelivery) -> None:
        """Send one delivery attempt. Updates status in DB."""
        payload_bytes = json.dumps(delivery.payload).encode()

        # Find subscription to get signing secret
        subs = await self._subs.get_by_event_type(delivery.event_type)
        secret = next(
            (s.secret for s in subs if s.client_id == delivery.client_id), ""
        )
        signature = sign_webhook_payload(payload_bytes, secret)

        headers = {
            "Content-Type": "application/json",
            "X-TrustLayer-Event": delivery.event_type,
            "X-TrustLayer-Signature": signature,
            "X-TrustLayer-Delivery": delivery.id,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    delivery.target_url,
                    content=payload_bytes,
                    headers=headers,
                )
            if 200 <= response.status_code < 300:
                delivery.mark_delivered(response.status_code)
                logger.info(
                    "Webhook delivered: %s → %s (%d)",
                    delivery.event_type,
                    delivery.target_url,
                    response.status_code,
                )
            else:
                delivery.mark_failed(settings.WEBHOOK_RETRY_DELAY_SECONDS)
                logger.warning(
                    "Webhook failed: %s → %s (%d) [attempt %d/%d]",
                    delivery.event_type,
                    delivery.target_url,
                    response.status_code,
                    delivery.attempts,
                    delivery.max_attempts,
                )
        except Exception as exc:
            delivery.mark_failed(settings.WEBHOOK_RETRY_DELAY_SECONDS)
            logger.error(
                "Webhook error: %s → %s: %s [attempt %d/%d]",
                delivery.event_type,
                delivery.target_url,
                exc,
                delivery.attempts,
                delivery.max_attempts,
            )

        await self._deliveries.update(delivery)
