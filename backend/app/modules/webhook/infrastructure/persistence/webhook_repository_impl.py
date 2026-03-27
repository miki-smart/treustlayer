from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.webhook.domain.entities.webhook_entities import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookSubscription,
)
from app.modules.webhook.domain.repositories.webhook_repositories import (
    WebhookDeliveryRepository,
    WebhookSubscriptionRepository,
)
from app.modules.webhook.infrastructure.persistence.webhook_model import (
    WebhookDeliveryModel,
    WebhookSubscriptionModel,
)


class SQLAlchemyWebhookSubscriptionRepository(WebhookSubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, sub: WebhookSubscription) -> WebhookSubscription:
        model = WebhookSubscriptionModel(
            id=sub.id,
            client_id=sub.client_id,
            event_type=sub.event_type,
            target_url=sub.target_url,
            secret=sub.secret,
            is_active=sub.is_active,
            created_at=sub.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _sub_to_entity(model)

    async def get_by_id(self, sub_id: str) -> Optional[WebhookSubscription]:
        model = await self._session.get(WebhookSubscriptionModel, sub_id)
        return _sub_to_entity(model) if model else None

    async def get_by_event_type(self, event_type: str) -> List[WebhookSubscription]:
        result = await self._session.execute(
            select(WebhookSubscriptionModel).where(
                and_(
                    WebhookSubscriptionModel.event_type == event_type,
                    WebhookSubscriptionModel.is_active.is_(True),
                )
            )
        )
        return [_sub_to_entity(m) for m in result.scalars().all()]

    async def get_by_client_id(self, client_id: str) -> List[WebhookSubscription]:
        result = await self._session.execute(
            select(WebhookSubscriptionModel).where(
                WebhookSubscriptionModel.client_id == client_id
            )
        )
        return [_sub_to_entity(m) for m in result.scalars().all()]

    async def deactivate(self, sub_id: str) -> None:
        await self._session.execute(
            update(WebhookSubscriptionModel)
            .where(WebhookSubscriptionModel.id == sub_id)
            .values(is_active=False)
        )
        await self._session.flush()

    async def list_all(self, skip: int = 0, limit: int = 50) -> List[WebhookSubscription]:
        result = await self._session.execute(
            select(WebhookSubscriptionModel)
            .order_by(WebhookSubscriptionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [_sub_to_entity(m) for m in result.scalars().all()]


class SQLAlchemyWebhookDeliveryRepository(WebhookDeliveryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, delivery: WebhookDelivery) -> WebhookDelivery:
        model = WebhookDeliveryModel(
            id=delivery.id,
            client_id=delivery.client_id,
            event_type=delivery.event_type,
            payload=delivery.payload,
            target_url=delivery.target_url,
            status=delivery.status.value,
            attempts=delivery.attempts,
            max_attempts=delivery.max_attempts,
            next_retry_at=delivery.next_retry_at,
            delivered_at=delivery.delivered_at,
            response_code=delivery.response_code,
            created_at=delivery.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _del_to_entity(model)

    async def update(self, delivery: WebhookDelivery) -> WebhookDelivery:
        model = await self._session.get(WebhookDeliveryModel, delivery.id)
        if not model:
            raise ValueError(f"Delivery {delivery.id} not found")
        model.status = delivery.status.value
        model.attempts = delivery.attempts
        model.next_retry_at = delivery.next_retry_at
        model.delivered_at = delivery.delivered_at
        model.response_code = delivery.response_code
        await self._session.flush()
        return _del_to_entity(model)

    async def get_pending(self, limit: int = 50) -> List[WebhookDelivery]:
        result = await self._session.execute(
            select(WebhookDeliveryModel)
            .where(WebhookDeliveryModel.status == DeliveryStatus.PENDING.value)
            .limit(limit)
        )
        return [_del_to_entity(m) for m in result.scalars().all()]

    async def get_retryable(
        self, as_of: datetime, limit: int = 50
    ) -> List[WebhookDelivery]:
        result = await self._session.execute(
            select(WebhookDeliveryModel)
            .where(
                and_(
                    WebhookDeliveryModel.status == DeliveryStatus.FAILED.value,
                    WebhookDeliveryModel.next_retry_at <= as_of,
                )
            )
            .limit(limit)
        )
        return [_del_to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, delivery_id: str) -> Optional[WebhookDelivery]:
        model = await self._session.get(WebhookDeliveryModel, delivery_id)
        return _del_to_entity(model) if model else None

    async def list_by_subscription(
        self, client_id: str, event_type: str, skip: int = 0, limit: int = 50
    ) -> List[WebhookDelivery]:
        result = await self._session.execute(
            select(WebhookDeliveryModel)
            .where(
                and_(
                    WebhookDeliveryModel.client_id == client_id,
                    WebhookDeliveryModel.event_type == event_type,
                )
            )
            .order_by(WebhookDeliveryModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [_del_to_entity(m) for m in result.scalars().all()]


def _sub_to_entity(model: WebhookSubscriptionModel) -> WebhookSubscription:
    return WebhookSubscription(
        id=str(model.id),
        client_id=str(model.client_id),
        event_type=str(model.event_type),
        target_url=str(model.target_url),
        secret=str(model.secret),
        is_active=bool(model.is_active),
        created_at=model.created_at,
    )


def _del_to_entity(model: WebhookDeliveryModel) -> WebhookDelivery:
    return WebhookDelivery(
        id=str(model.id),
        client_id=str(model.client_id),
        event_type=str(model.event_type),
        payload=dict(model.payload) if model.payload else {},
        target_url=str(model.target_url),
        status=DeliveryStatus(model.status),
        attempts=int(model.attempts),
        max_attempts=int(model.max_attempts),
        next_retry_at=model.next_retry_at,
        delivered_at=model.delivered_at,
        response_code=model.response_code,
        created_at=model.created_at,
    )
