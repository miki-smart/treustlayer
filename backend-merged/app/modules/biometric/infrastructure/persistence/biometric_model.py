"""
BiometricModel — SQLAlchemy ORM model for biometric.records table.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class BiometricModel(Base):
    __tablename__ = "records"
    __table_args__ = {"schema": "biometric"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    
    liveness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    spoof_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    
    device_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    biometric_data_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    biometric_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
