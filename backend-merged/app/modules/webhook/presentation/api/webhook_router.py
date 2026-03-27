"""
Webhook router � event subscriptions and delivery tracking.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import DBSession, CurrentUserId
from app.modules.webhook.infrastructure.persistence.webhook_repository_impl import SQLAlchemyWebhookRepository
from app.modules.app_registry.infrastructure.persistence.app_repository_impl import SQLAlchemyAppRepository
from app.modules.webhook.application.use_cases.subscribe_webhook import SubscribeWebhookUseCase

router = APIRouter()


class WebhookSubscriptionResponse(BaseModel):
    id: str
    client_id: str
    event_type: str
    target_url: str
    secret: Optional[str] = None
    is_active: bool
    created_at: str


class WebhookDeliveryResponse(BaseModel):
    id: str
    subscription_id: str
    event_type: str
    target_url: str
    status: str
    attempts: int
    last_attempt_at: Optional[str]
    next_retry_at: Optional[str]
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: str


class SubscribeRequest(BaseModel):
    client_id: str
    event_type: str
    target_url: str


@router.post("/subscribe", response_model=WebhookSubscriptionResponse, status_code=201)
async def subscribe_webhook(
    payload: SubscribeRequest,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Subscribe to webhook events.
    
    Returns subscription with webhook secret (only shown once).
    """
    webhook_repo = SQLAlchemyWebhookRepository(session)
    app_repo = SQLAlchemyAppRepository(session)
    
    use_case = SubscribeWebhookUseCase(webhook_repo, app_repo)
    subscription, webhook_secret = await use_case.execute(
        payload.client_id, payload.event_type, payload.target_url
    )
    
    await session.commit()
    
    return WebhookSubscriptionResponse(
        id=subscription.id,
        client_id=subscription.client_id,
        event_type=subscription.event_type,
        target_url=subscription.target_url,
        secret=webhook_secret,
        is_active=subscription.is_active,
        created_at=subscription.created_at.isoformat(),
    )


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def list_subscriptions(
    client_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    List webhook subscriptions for a client.
    """
    webhook_repo = SQLAlchemyWebhookRepository(session)
    subscriptions = await webhook_repo.list_subscriptions_by_client(client_id)
    
    return [
        WebhookSubscriptionResponse(
            id=sub.id,
            client_id=sub.client_id,
            event_type=sub.event_type,
            target_url=sub.target_url,
            is_active=sub.is_active,
            created_at=sub.created_at.isoformat(),
        )
        for sub in subscriptions
    ]


@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def unsubscribe(
    subscription_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Unsubscribe from webhook events.
    """
    webhook_repo = SQLAlchemyWebhookRepository(session)
    
    subscription = await webhook_repo.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    await webhook_repo.delete_subscription(subscription_id)
    await session.commit()
    
    return None


@router.get("/deliveries/{subscription_id}", response_model=List[WebhookDeliveryResponse])
async def list_deliveries(
    subscription_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
    skip: int = 0,
    limit: int = 50,
):
    """
    List webhook deliveries for a subscription.
    """
    webhook_repo = SQLAlchemyWebhookRepository(session)
    deliveries = await webhook_repo.list_deliveries_by_subscription(subscription_id, skip, limit)
    
    return [
        WebhookDeliveryResponse(
            id=delivery.id,
            subscription_id=delivery.subscription_id,
            event_type=delivery.event_type,
            target_url=delivery.target_url,
            status=delivery.status.value,
            attempts=delivery.attempts,
            last_attempt_at=delivery.last_attempt_at.isoformat() if delivery.last_attempt_at else None,
            next_retry_at=delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
            response_status=delivery.response_status,
            error_message=delivery.error_message,
            created_at=delivery.created_at.isoformat(),
        )
        for delivery in deliveries
    ]


@router.post("/retry/{delivery_id}", response_model=WebhookDeliveryResponse)
async def retry_delivery(
    delivery_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Manually retry a failed webhook delivery.
    """
    webhook_repo = SQLAlchemyWebhookRepository(session)
    
    delivery = await webhook_repo.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    delivery.status = DeliveryStatus.PENDING
    delivery.next_retry_at = None
    await webhook_repo.update_delivery(delivery)
    
    await session.commit()
    
    return WebhookDeliveryResponse(
        id=delivery.id,
        subscription_id=delivery.subscription_id,
        event_type=delivery.event_type,
        target_url=delivery.target_url,
        status=delivery.status.value,
        attempts=delivery.attempts,
        last_attempt_at=delivery.last_attempt_at.isoformat() if delivery.last_attempt_at else None,
        next_retry_at=delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
        response_status=delivery.response_status,
        error_message=delivery.error_message,
        created_at=delivery.created_at.isoformat(),
    )
