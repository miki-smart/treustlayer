"""
Audit SQLAlchemy model.
"""
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class AuditEntryModel(Base):
    """Audit entry ORM model (append-only)."""
    
    __tablename__ = "audit_entries"
    __table_args__ = {"schema": "audit"}
    
    id = Column(UUID, primary_key=True)
    actor_id = Column(UUID, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(UUID, nullable=True, index=True)
    # Python name cannot be "metadata" — reserved on Declarative API; DB column stays "metadata".
    audit_metadata = Column("metadata", JSONB, nullable=False, server_default="{}")
    changes = Column(JSONB, nullable=False, server_default="{}")
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
