"""
Consent SQLAlchemy model.
"""
from sqlalchemy import ARRAY, Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ConsentRecordModel(Base):
    """Consent record ORM model."""
    
    __tablename__ = "consent_records"
    __table_args__ = {"schema": "consent"}
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, nullable=False, index=True)
    client_id = Column(String(120), nullable=False, index=True)
    scopes = Column(ARRAY(String), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    granted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
