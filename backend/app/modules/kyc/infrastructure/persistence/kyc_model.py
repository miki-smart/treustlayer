import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.db.base import Base


class KYCVerificationModel(Base):
    __tablename__ = "verifications"
    __table_args__ = {"schema": "kyc"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default="pending")
    tier = Column(String(20), nullable=False, default="tier_0")
    trust_score = Column(Integer, nullable=False, default=0)
    document_type = Column(String(100), nullable=True)
    document_number = Column(String(100), nullable=True)
    document_url = Column(String(512), nullable=True)
    face_similarity_score = Column(Float, nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
