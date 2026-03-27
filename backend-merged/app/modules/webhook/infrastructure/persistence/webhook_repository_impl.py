"""
SQLAlchemy implementation of WebhookRepository.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.webhook.domain.entities.webhook_subscription import WebhookSubscription
from app.modules.webhook.domain.entities.webhook_delivery import WebhookDelivery, DeliveryStatus
from app.modules.webhook.domain.repositories.webhook_repository import WebhookRepository
from app.modules.webhook.infrastructure.persistence.webhook_model import (
    WebhookSubscriptionModel,
    WebhookDeliveryModel,
)


class SQLAlchemyWebhookRepository(WebhookRepository):
    """SQLAlchemy implementation of webhook repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Create new webhook subscription."""
        model = WebhookSubscriptionModel(
            id=subscription.id,
            client_id=subscription.client_id,
            event_type=subscription.event_type,
            target_url=subscription.target_url,
            secret=subscription.secret,
            is_active=subscription.is_active,
        )
        self.session.add(model)
        await self.session.flush()
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID."""
        result = await self.session.execute(
            select(WebhookSubscriptionModel).where(WebhookSubscriptionModel.id == subscription_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._subscription_model_to_entity(model)
    
    async def list_subscriptions_by_client(self, client_id: str) -> List[WebhookSubscription]:
        """List subscriptions for a client."""
        result = await self.session.execute(
            select(WebhookSubscriptionModel)
            .where(WebhookSubscriptionModel.client_id == client_id)
            .order_by(WebhookSubscriptionModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._subscription_model_to_entity(m) for m in models]
    
    async def list_subscriptions_by_event(self, event_type: str) -> List[WebhookSubscription]:
        """List active subscriptions for an event type."""
        result = await self.session.execute(
            select(WebhookSubscriptionModel).where(
                WebhookSubscriptionModel.event_type == event_type,
                WebhookSubscriptionModel.is_active == True,
            )
        )
        models = result.scalars().all()
        return [self._subscription_model_to_entity(m) for m in models]
    
    async def update_subscription(self, subscription: WebhookSubscription) -> WebhookSubscription:
        """Update subscription."""
        result = await self.session.execute(
            select(WebhookSubscriptionModel).where(WebhookSubscriptionModel.id == subscription.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.is_active = subscription.is_active
            model.updated_at = subscription.updated_at
            await self.session.flush()
        return subscription
    
    async def delete_subscription(self, subscription_id: str) -> None:
        """Delete subscription."""
        await self.session.execute(
            delete(WebhookSubscriptionModel).where(WebhookSubscriptionModel.id == subscription_id)
        )
        await self.session.flush()
    
    async def create_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Create new delivery record."""
        model = WebhookDeliveryModel(
            id=delivery.id,
            subscription_id=delivery.subscription_id,
            event_type=delivery.event_type,
            payload=delivery.payload,
            target_url=delivery.target_url,
            status=delivery.status.value,
            attempts=delivery.attempts,
            last_attempt_at=delivery.last_attempt_at,
            next_retry_at=delivery.next_retry_at,
            response_status=delivery.response_status,
            response_body=delivery.response_body,
            error_message=delivery.error_message,
        )
        self.session.add(model)
        await self.session.flush()
        return delivery
    
    async def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID."""
        result = await self.session.execute(
            select(WebhookDeliveryModel).where(WebhookDeliveryModel.id == delivery_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._delivery_model_to_entity(model)
    
    async def list_deliveries_by_subscription(
        self, subscription_id: str, skip: int = 0, limit: int = 50
    ) -> List[WebhookDelivery]:
        """List deliveries for a subscription."""
        result = await self.session.execute(
            select(WebhookDeliveryModel)
            .where(WebhookDeliveryModel.subscription_id == subscription_id)
            .order_by(WebhookDeliveryModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._delivery_model_to_entity(m) for m in models]
    
    async def list_pending_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """List pending/retrying deliveries for worker."""
        result = await self.session.execute(
            select(WebhookDeliveryModel)
            .where(
                WebhookDeliveryModel.status.in_(["pending", "retrying"]),
                (WebhookDeliveryModel.next_retry_at.is_(None))
                | (WebhookDeliveryModel.next_retry_at <= datetime.now(timezone.utc)),
            )
            .order_by(WebhookDeliveryModel.created_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._delivery_model_to_entity(m) for m in models]
    
    async def update_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Update delivery record."""
        result = await self.session.execute(
            select(WebhookDeliveryModel).where(WebhookDeliveryModel.id == delivery.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = delivery.status.value
            model.attempts = delivery.attempts
            model.last_attempt_at = delivery.last_attempt_at
            model.next_retry_at = delivery.next_retry_at
            model.response_status = delivery.response_status
            model.response_body = delivery.response_body
            model.error_message = delivery.error_message
            await self.session.flush()
        return delivery
    
    def _subscription_model_to_entity(self, model: WebhookSubscriptionModel) -> WebhookSubscription:
        """Convert subscription model to entity."""
        return WebhookSubscription(
            id=str(model.id),
            client_id=model.client_id,
            event_type=model.event_type,
            target_url=model.target_url,
            secret=model.secret,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _delivery_model_to_entity(self, model: WebhookDeliveryModel) -> WebhookDelivery:
        """Convert delivery model to entity."""
        return WebhookDelivery(
            id=str(model.id),
            subscription_id=str(model.subscription_id),
            event_type=model.event_type,
            payload=model.payload,
            target_url=model.target_url,
            status=DeliveryStatus(model.status),
            attempts=model.attempts,
            last_attempt_at=model.last_attempt_at,
            next_retry_at=model.next_retry_at,
            response_status=model.response_status,
            response_body=model.response_body,
            error_message=model.error_message,
            created_at=model.created_at,
        )
