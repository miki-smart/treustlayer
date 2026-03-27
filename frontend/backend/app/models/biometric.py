import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class BiometricType(str, enum.Enum):
    face = "face"
    voice = "voice"


class BiometricStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    failed = "failed"
    flagged = "flagged"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class BiometricRecord(Base):
    __tablename__ = "biometric_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[BiometricType] = mapped_column(Enum(BiometricType), nullable=False)
    status: Mapped[BiometricStatus] = mapped_column(Enum(BiometricStatus), nullable=False, default=BiometricStatus.pending)
    liveness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    spoof_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False, default=RiskLevel.medium)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="biometric_records")
