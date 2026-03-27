"""
Webhook router — event subscriptions and delivery tracking.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from app.api.dependencies import DBSession, CurrentUserId

router = APIRouter()


class WebhookSubscriptionResponse(BaseModel):
    id: str
    client_id: str
    event_type: str
    target_url: str
    is_active: bool
    created_at: str


@router.post("/subscribe", response_model=WebhookSubscriptionResponse, status_code=201)
async def subscribe_webhook(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Subscribe to webhook events. Stub implementation."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def list_subscriptions(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """List webhook subscriptions. Stub implementation."""
    return []


@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def unsubscribe(
    subscription_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Unsubscribe from webhook. Stub implementation."""
    return None
