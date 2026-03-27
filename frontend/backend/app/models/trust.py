import uuid
from datetime import datetime
from sqlalchemy import Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class TrustProfile(Base):
    """
    Computed trust profile for each user.
    Re-evaluated whenever KYC or biometric status changes.

    KYC Tiers:
      0 - No verification
      1 - Email/phone verified
      2 - Document verified (ID + address proof)
      3 - Full biometric verification passed
    """
    __tablename__ = "trust_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    kyc_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # JSON breakdown: {email_verified, phone_verified, kyc_approved, biometric_verified, ...}
    factors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_evaluated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship()
