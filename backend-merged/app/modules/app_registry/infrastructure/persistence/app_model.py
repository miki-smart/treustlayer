"""
App SQLAlchemy model.
"""
from sqlalchemy import ARRAY, Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class AppModel(Base):
    """OAuth2 client application ORM model."""
    
    __tablename__ = "apps"
    __table_args__ = {"schema": "app_registry"}
    
    id = Column(UUID, primary_key=True)
    name = Column(String(200), nullable=False)
    owner_id = Column(UUID, nullable=False, index=True)
    client_id = Column(String(120), nullable=False, unique=True, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    allowed_scopes = Column(ARRAY(String), nullable=False)
    redirect_uris = Column(ARRAY(String), nullable=False)
    description = Column(Text, nullable=False, server_default="")
    logo_url = Column(String(512), nullable=True)
    category = Column(String(50), nullable=False, server_default="general")
    is_active = Column(Boolean, nullable=False, server_default="true")
    is_approved = Column(Boolean, nullable=False, server_default="false")
    is_public = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
