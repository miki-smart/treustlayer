import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.infrastructure.db.base import Base


class AuthorizationCodeModel(Base):
    __tablename__ = "authorization_codes"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(120), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    redirect_uri = Column(String(512), nullable=False)
    scopes = Column(ARRAY(String), nullable=False, default=list)
    code_challenge = Column(String(256), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
