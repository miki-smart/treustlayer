"""
Event handlers — wires domain events to cross-module side effects.

Subscriptions are registered at application startup.
Each handler receives a DomainEvent and uses a fresh DB session.

Design: handlers are plain async functions that open their own DB session.
This isolates them from the request cycle and makes them independently retryable.
"""
import logging

from app.core.database import AsyncSessionLocal
from app.core.events import event_bus

logger = logging.getLogger(__name__)


async def _dispatch_webhook(event_type: str, payload: dict) -> None:
    """
    Helper to dispatch webhook events.
    Will be implemented once webhook module is ready.
    """
    try:
        async with AsyncSessionLocal() as session:
            from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import (
                SQLAlchemyWebhookDeliveryRepository,
                SQLAlchemyWebhookSubscriptionRepository,
            )
            from app.modules.webhook.application.services.webhook_service import WebhookService
            
            svc = WebhookService(
                SQLAlchemyWebhookSubscriptionRepository(session),
                SQLAlchemyWebhookDeliveryRepository(session),
            )
            await svc.dispatch_event(event_type, payload)
            await session.commit()
    except Exception as exc:
        logger.error("Failed to dispatch webhook for %s: %s", event_type, exc)


def register_event_handlers() -> None:
    """
    Called once at application startup to register all domain event handlers.
    
    Handlers will be registered as modules are implemented:
    - UserCreatedEvent → dispatch webhook
    - KYCApprovedEvent → dispatch webhook + update trust score
    - ConsentRevokedEvent → revoke refresh tokens + dispatch webhook
    - TrustScoreUpdatedEvent → dispatch webhook
    """
    logger.info("Event handlers will be registered as modules are implemented")
