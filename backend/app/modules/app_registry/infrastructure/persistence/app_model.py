import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.infrastructure.db.base import Base


class RegisteredAppModel(Base):
    __tablename__ = "apps"
    __table_args__ = {"schema": "app_registry"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    client_id = Column(String(120), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=True, index=True)
    owner_id = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    allowed_scopes = Column(ARRAY(String), nullable=False, default=list)
    redirect_uris = Column(ARRAY(String), nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
