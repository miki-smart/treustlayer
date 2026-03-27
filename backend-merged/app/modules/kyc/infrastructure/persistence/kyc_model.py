"""
KYCModel — SQLAlchemy ORM model for kyc.verifications table.
Enhanced with all frontend fields.
"""
import uuid
from datetime import datetime, timezone, date

from sqlalchemy import String, Float, Integer, DateTime, Text, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class KYCModel(Base):
    __tablename__ = "verifications"
    __table_args__ = {"schema": "kyc"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="tier_0", index=True)
    
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bill_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    account_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    mrz_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mrz_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    id_front_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    id_back_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    utility_bill_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    face_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    documents_submitted: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    id_ocr_confidence: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    utility_ocr_confidence: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    synthetic_id_probability: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    face_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
