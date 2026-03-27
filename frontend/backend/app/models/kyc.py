import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Enum, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import enum


class KYCStatus(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    flagged = "flagged"


class KYCApplication(Base):
    __tablename__ = "kyc_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[KYCStatus] = mapped_column(Enum(KYCStatus), nullable=False, default=KYCStatus.pending)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    documents_submitted: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    ocr_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    synthetic_id_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # TrustLayer ID API spec fields
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    face_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # tier: tier_0, tier_1, tier_2, tier_3
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="tier_0")
    face_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="kyc_applications")
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewer_id])
