"""
Webhook background worker — polls the DB queue and dispatches pending deliveries.
Runs as an asyncio background task started at app startup.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.core.database import AsyncSessionLocal
from app.modules.webhook.application.services.webhook_service import WebhookService
from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import (
    SQLAlchemyWebhookDeliveryRepository,
    SQLAlchemyWebhookSubscriptionRepository,
)

logger = logging.getLogger(__name__)

_worker_running = False


async def run_webhook_worker(interval_seconds: int = 10) -> None:
    """
    Continuously polls for pending/retryable webhook deliveries and processes them.
    """
    global _worker_running
    _worker_running = True
    logger.info("Webhook worker started (interval=%ds)", interval_seconds)

    while _worker_running:
        try:
            await _process_batch()
        except Exception as exc:
            logger.error("Webhook worker error: %s", exc, exc_info=True)
        await asyncio.sleep(interval_seconds)


async def _process_batch() -> None:
    async with AsyncSessionLocal() as session:
        sub_repo = SQLAlchemyWebhookSubscriptionRepository(session)
        del_repo = SQLAlchemyWebhookDeliveryRepository(session)
        svc = WebhookService(sub_repo, del_repo)

        # Pending (first attempt)
        pending = await del_repo.get_pending(limit=50)
        # Retryable (failed but scheduled for retry)
        retryable = await del_repo.get_retryable(as_of=datetime.now(timezone.utc), limit=50)

        for delivery in pending + retryable:
            await svc.process_delivery(delivery)

        await session.commit()


def stop_webhook_worker() -> None:
    global _worker_running
    _worker_running = False
