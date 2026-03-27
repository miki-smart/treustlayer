"""
TrustModel — SQLAlchemy ORM model for trust.profiles table.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class TrustModel(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "trust"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    kyc_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    face_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    digital_identity_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    factors: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_evaluated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
