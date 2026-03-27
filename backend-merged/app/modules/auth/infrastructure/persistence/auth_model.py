"""
Auth SQLAlchemy models.
"""
from sqlalchemy import ARRAY, Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class AuthorizationCodeModel(Base):
    """Authorization code ORM model."""
    
    __tablename__ = "authorization_codes"
    __table_args__ = {"schema": "auth"}
    
    id = Column(UUID, primary_key=True)
    code = Column(String(100), nullable=False, unique=True, index=True)
    client_id = Column(String(120), nullable=False)
    user_id = Column(UUID, nullable=False, index=True)
    redirect_uri = Column(String(512), nullable=False)
    scopes = Column(ARRAY(String), nullable=False)
    code_challenge = Column(String(256), nullable=True)
    code_challenge_method = Column(String(10), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RefreshTokenModel(Base):
    """Refresh token ORM model."""
    
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "session"}
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, nullable=False, index=True)
    client_id = Column(String(120), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    scopes = Column(ARRAY(String), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
