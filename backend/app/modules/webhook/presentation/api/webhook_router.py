import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role
from app.core.database import get_async_session
from app.modules.identity.domain.entities.user import UserRole
from app.modules.webhook.domain.entities.webhook_entities import (
    DeliveryStatus,
    WebhookSubscription,
)
from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import (
    SQLAlchemyWebhookDeliveryRepository,
    SQLAlchemyWebhookSubscriptionRepository,
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class WebhookSubscribeRequest(BaseModel):
    client_id: str
    event_type: str
    target_url: str


class WebhookSubscriptionResponse(BaseModel):
    id: str
    client_id: str
    event_type: str
    target_url: str
    signing_secret: Optional[str] = None  # only returned at creation
    is_active: bool
    created_at: datetime


class WebhookDeliveryResponse(BaseModel):
    id: str
    client_id: str
    event_type: str
    target_url: str
    status: str
    attempts: int
    max_attempts: int
    delivered_at: Optional[datetime]
    response_code: Optional[int]
    created_at: datetime


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/subscribe",
    response_model=WebhookSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe a client app to a domain event type",
)
async def subscribe_webhook(
    payload: WebhookSubscribeRequest,
    session: AsyncSession = Depends(get_async_session),
):
    signing_secret = secrets.token_urlsafe(32)
    sub = WebhookSubscription(
        client_id=payload.client_id,
        event_type=payload.event_type,
        target_url=payload.target_url,
        secret=signing_secret,
    )
    repo = SQLAlchemyWebhookSubscriptionRepository(session)
    sub = await repo.create(sub)
    await session.commit()

    return WebhookSubscriptionResponse(
        id=sub.id,
        client_id=sub.client_id,
        event_type=sub.event_type,
        target_url=sub.target_url,
        signing_secret=signing_secret,  # only returned once
        is_active=sub.is_active,
        created_at=sub.created_at,
    )


@router.delete(
    "/subscriptions/{sub_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a webhook subscription",
)
async def deactivate_subscription(
    sub_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyWebhookSubscriptionRepository(session)
    await repo.deactivate(sub_id)
    await session.commit()


@router.get(
    "/subscriptions",
    response_model=List[WebhookSubscriptionResponse],
    summary="[Admin] List all webhook subscriptions",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_subscriptions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyWebhookSubscriptionRepository(session)
    subs = await repo.list_all(skip=skip, limit=limit)
    return [
        WebhookSubscriptionResponse(
            id=s.id,
            client_id=s.client_id,
            event_type=s.event_type,
            target_url=s.target_url,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in subs
    ]


@router.get(
    "/deliveries",
    response_model=List[WebhookDeliveryResponse],
    summary="List pending webhook deliveries (admin)",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_pending_deliveries(
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyWebhookDeliveryRepository(session)
    deliveries = await repo.get_pending(limit=100)
    return [
        WebhookDeliveryResponse(
            id=d.id,
            client_id=d.client_id,
            event_type=d.event_type,
            target_url=d.target_url,
            status=d.status.value,
            attempts=d.attempts,
            max_attempts=d.max_attempts,
            delivered_at=d.delivered_at,
            response_code=d.response_code,
            created_at=d.created_at,
        )
        for d in deliveries
    ]


@router.get(
    "/deliveries/{delivery_id}",
    response_model=WebhookDeliveryResponse,
    summary="[Admin] Get a specific webhook delivery by ID",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def get_delivery(
    delivery_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyWebhookDeliveryRepository(session)
    d = await repo.get_by_id(delivery_id)
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )
    return WebhookDeliveryResponse(
        id=d.id,
        client_id=d.client_id,
        event_type=d.event_type,
        target_url=d.target_url,
        status=d.status.value,
        attempts=d.attempts,
        max_attempts=d.max_attempts,
        delivered_at=d.delivered_at,
        response_code=d.response_code,
        created_at=d.created_at,
    )


@router.post(
    "/retry/{delivery_id}",
    response_model=WebhookDeliveryResponse,
    summary="[Admin] Retry a failed webhook delivery",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def retry_delivery(
    delivery_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    repo = SQLAlchemyWebhookDeliveryRepository(session)
    d = await repo.get_by_id(delivery_id)
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )
    if d.status == DeliveryStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery was already delivered successfully",
        )
    # Reset to PENDING so the worker picks it up again
    d.status = DeliveryStatus.PENDING
    d.next_retry_at = None
    updated = await repo.update(d)
    await session.commit()
    return WebhookDeliveryResponse(
        id=updated.id,
        client_id=updated.client_id,
        event_type=updated.event_type,
        target_url=updated.target_url,
        status=updated.status.value,
        attempts=updated.attempts,
        max_attempts=updated.max_attempts,
        delivered_at=updated.delivered_at,
        response_code=updated.response_code,
        created_at=updated.created_at,
    )


@router.get(
    "/subscriptions/{sub_id}/deliveries",
    response_model=List[WebhookDeliveryResponse],
    summary="[Admin] List deliveries for a specific subscription",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_deliveries_for_subscription(
    sub_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    sub_repo = SQLAlchemyWebhookSubscriptionRepository(session)
    sub = await sub_repo.get_by_id(sub_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    del_repo = SQLAlchemyWebhookDeliveryRepository(session)
    deliveries = await del_repo.list_by_subscription(
        client_id=sub.client_id,
        event_type=sub.event_type,
        skip=skip,
        limit=limit,
    )
    return [
        WebhookDeliveryResponse(
            id=d.id,
            client_id=d.client_id,
            event_type=d.event_type,
            target_url=d.target_url,
            status=d.status.value,
            attempts=d.attempts,
            max_attempts=d.max_attempts,
            delivered_at=d.delivered_at,
            response_code=d.response_code,
            created_at=d.created_at,
        )
        for d in deliveries
    ]
