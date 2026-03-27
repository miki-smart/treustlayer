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

# Domain event imports
from app.modules.consent.domain.events.consent_events import ConsentRevokedEvent
from app.modules.identity.domain.events.user_events import UserCreatedEvent
from app.modules.kyc.domain.events.kyc_events import KYCApprovedEvent, RiskUpdatedEvent

# Infrastructure
from app.modules.session.infrastructure.persistence.refresh_token_repository_impl import (
    SQLAlchemyRefreshTokenRepository,
)
from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import (
    SQLAlchemyWebhookDeliveryRepository,
    SQLAlchemyWebhookSubscriptionRepository,
)
from app.modules.webhook.application.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


# ── Handlers ─────────────────────────────────────────────────────────────────

async def on_user_created(event: UserCreatedEvent) -> None:
    """Dispatch webhook for user.created event."""
    await _dispatch_webhook(
        "UserCreatedEvent",
        {
            "user_id": event.user_id,
            "email": event.email,
            "username": event.username,
            "occurred_at": event.occurred_at.isoformat(),
        },
    )


async def on_kyc_approved(event: KYCApprovedEvent) -> None:
    """Dispatch webhook for kyc.approved event."""
    await _dispatch_webhook(
        "KYCApprovedEvent",
        {
            "user_id": event.user_id,
            "kyc_id": event.kyc_id,
            "tier": event.tier,
            "trust_score": event.trust_score,
            "occurred_at": event.occurred_at.isoformat(),
        },
    )


async def on_risk_updated(event: RiskUpdatedEvent) -> None:
    """Dispatch webhook for risk.updated event."""
    await _dispatch_webhook(
        "RiskUpdatedEvent",
        {
            "user_id": event.user_id,
            "trust_score": event.trust_score,
            "risk_flag": event.risk_flag,
            "occurred_at": event.occurred_at.isoformat(),
        },
    )


async def on_consent_revoked(event: ConsentRevokedEvent) -> None:
    """
    When consent is revoked, invalidate all refresh tokens for that user/client pair.
    Also dispatch webhook.
    """
    logger.info(
        "Consent revoked: user=%s client=%s — revoking refresh tokens",
        event.user_id,
        event.client_id,
    )
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyRefreshTokenRepository(session)
        await repo.revoke_all_for_user_client(event.user_id, event.client_id)
        await session.commit()

    await _dispatch_webhook(
        "ConsentRevokedEvent",
        {
            "user_id": event.user_id,
            "client_id": event.client_id,
            "consent_id": event.consent_id,
            "occurred_at": event.occurred_at.isoformat(),
        },
    )


# ── Webhook dispatch helper ───────────────────────────────────────────────────

async def _dispatch_webhook(event_type: str, payload: dict) -> None:
    try:
        async with AsyncSessionLocal() as session:
            svc = WebhookService(
                SQLAlchemyWebhookSubscriptionRepository(session),
                SQLAlchemyWebhookDeliveryRepository(session),
            )
            await svc.dispatch_event(event_type, payload)
            await session.commit()
    except Exception as exc:
        logger.error("Failed to dispatch webhook for %s: %s", event_type, exc)


# ── Registration ──────────────────────────────────────────────────────────────

def register_event_handlers() -> None:
    """Called once at application startup to register all domain event handlers."""
    event_bus.subscribe(UserCreatedEvent, on_user_created)
    event_bus.subscribe(KYCApprovedEvent, on_kyc_approved)
    event_bus.subscribe(RiskUpdatedEvent, on_risk_updated)
    event_bus.subscribe(ConsentRevokedEvent, on_consent_revoked)
    logger.info("Event handlers registered")
