"""
Webhook SQLAlchemy models.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class WebhookSubscriptionModel(Base):
    """Webhook subscription ORM model."""
    
    __tablename__ = "webhook_subscriptions"
    __table_args__ = {"schema": "webhook"}
    
    id = Column(UUID, primary_key=True)
    client_id = Column(String(120), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    target_url = Column(String(512), nullable=False)
    secret = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class WebhookDeliveryModel(Base):
    """Webhook delivery ORM model."""
    
    __tablename__ = "webhook_deliveries"
    __table_args__ = {"schema": "webhook"}
    
    id = Column(UUID, primary_key=True)
    subscription_id = Column(UUID, nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    target_url = Column(String(512), nullable=False)
    status = Column(String(20), nullable=False, server_default="pending", index=True)
    attempts = Column(Integer, nullable=False, server_default="0")
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
