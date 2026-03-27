"""
Webhook management — /api/v1/webhooks/*
"""
import uuid
import secrets
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, AdminUser, DB
from app.models.webhook_subscription import WebhookSubscription, WebhookDeliveryNew

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

SUPPORTED_EVENTS = [
    "kyc.submitted", "kyc.approved", "kyc.rejected", "kyc.flagged",
    "risk.alert", "consent.granted", "consent.revoked",
    "identity.updated", "user.registered", "user.deactivated",
]


class WebhookSubscribeRequest(BaseModel):
    client_id: str
    event_type: str
    target_url: str


class WebhookSubscriptionResponse(BaseModel):
    id: str
    client_id: str
    event_type: str
    target_url: str
    signing_secret: str | None = None
    is_active: bool
    created_at: str


class WebhookDeliveryResponse(BaseModel):
    id: str
    client_id: str
    event_type: str
    target_url: str
    status: str
    attempts: int
    max_attempts: int
    delivered_at: str | None = None
    response_code: int | None = None
    created_at: str


def _sub_out(s: WebhookSubscription, include_secret: bool = False) -> WebhookSubscriptionResponse:
    return WebhookSubscriptionResponse(
        id=str(s.id),
        client_id=s.client_id,
        event_type=s.event_type,
        target_url=s.target_url,
        signing_secret=s.signing_secret if include_secret else None,
        is_active=s.is_active,
        created_at=s.created_at.isoformat() if s.created_at else "",
    )


def _del_out(d: WebhookDeliveryNew) -> WebhookDeliveryResponse:
    return WebhookDeliveryResponse(
        id=str(d.id),
        client_id=d.client_id,
        event_type=d.event_type,
        target_url=d.target_url,
        status=d.status,
        attempts=d.attempts,
        max_attempts=d.max_attempts,
        delivered_at=d.delivered_at.isoformat() if d.delivered_at else None,
        response_code=d.response_code,
        created_at=d.created_at.isoformat() if d.created_at else "",
    )


@router.post("/subscribe", response_model=WebhookSubscriptionResponse, status_code=201, summary="Subscribe a client app to a domain event type")
async def subscribe_webhook(body: WebhookSubscribeRequest, db: DB):
    if body.event_type not in SUPPORTED_EVENTS:
        raise HTTPException(status_code=400, detail=f"Unknown event_type. Supported: {SUPPORTED_EVENTS}")
    sub = WebhookSubscription(
        id=uuid.uuid4(),
        client_id=body.client_id,
        event_type=body.event_type,
        target_url=body.target_url,
        signing_secret=secrets.token_hex(32),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(sub)
    await db.flush()
    return _sub_out(sub, include_secret=True)


@router.delete("/subscriptions/{sub_id}", status_code=204, summary="Deactivate a webhook subscription")
async def deactivate_subscription(sub_id: str, db: DB):
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == uuid.UUID(sub_id)))
    sub = result.scalar_one_or_none()
    if sub:
        sub.is_active = False


@router.get("/subscriptions", response_model=list[WebhookSubscriptionResponse], summary="[Admin] List all webhook subscriptions")
async def list_subscriptions(
    current_user: AdminUser, db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(
        select(WebhookSubscription)
        .order_by(WebhookSubscription.created_at.desc())
        .offset(skip).limit(limit)
    )
    return [_sub_out(s) for s in result.scalars().all()]


@router.get("/deliveries", response_model=list[WebhookDeliveryResponse], summary="List pending webhook deliveries (admin)")
async def list_pending_deliveries(current_user: AdminUser, db: DB):
    result = await db.execute(
        select(WebhookDeliveryNew)
        .where(WebhookDeliveryNew.status == "pending")
        .order_by(WebhookDeliveryNew.created_at.desc())
        .limit(100)
    )
    return [_del_out(d) for d in result.scalars().all()]


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse, summary="[Admin] Get a specific webhook delivery by ID")
async def get_delivery(delivery_id: str, current_user: AdminUser, db: DB):
    result = await db.execute(
        select(WebhookDeliveryNew).where(WebhookDeliveryNew.id == uuid.UUID(delivery_id))
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return _del_out(d)


@router.post("/retry/{delivery_id}", response_model=WebhookDeliveryResponse, summary="[Admin] Retry a failed webhook delivery")
async def retry_delivery(delivery_id: str, current_user: AdminUser, db: DB):
    result = await db.execute(
        select(WebhookDeliveryNew).where(WebhookDeliveryNew.id == uuid.UUID(delivery_id))
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    d.status = "pending"
    d.attempts = 0
    return _del_out(d)


@router.get("/subscriptions/{sub_id}/deliveries", response_model=list[WebhookDeliveryResponse], summary="[Admin] List deliveries for a specific subscription")
async def list_deliveries_for_subscription(
    sub_id: str, current_user: AdminUser, db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(
        select(WebhookDeliveryNew)
        .where(WebhookDeliveryNew.subscription_id == uuid.UUID(sub_id))
        .order_by(WebhookDeliveryNew.created_at.desc())
        .offset(skip).limit(limit)
    )
    return [_del_out(d) for d in result.scalars().all()]
