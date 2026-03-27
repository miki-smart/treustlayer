import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import enum


class SSOProtocol(str, enum.Enum):
    oauth2 = "oauth2"
    openid_connect = "openid_connect"
    saml = "saml"


class SSOProviderStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"


class SSOSessionStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"


class ConsentStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class SSOProvider(Base):
    __tablename__ = "sso_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    protocol: Mapped[SSOProtocol] = mapped_column(Enum(SSOProtocol), nullable=False)
    status: Mapped[SSOProviderStatus] = mapped_column(Enum(SSOProviderStatus), nullable=False, default=SSOProviderStatus.pending)
    connected_at: Mapped[str] = mapped_column(String(50), nullable=False)
    last_sync: Mapped[str | None] = mapped_column(String(50), nullable=True)
    users_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    sessions: Mapped[list["SSOSession"]] = relationship(back_populates="provider", cascade="all, delete-orphan")
    consents: Mapped[list["ConsentRecord"]] = relationship(back_populates="provider", cascade="all, delete-orphan")


class SSOSession(Base):
    __tablename__ = "sso_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sso_providers.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    device: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[SSOSessionStatus] = mapped_column(Enum(SSOSessionStatus), nullable=False, default=SSOSessionStatus.active)

    user: Mapped["User"] = relationship(back_populates="sso_sessions")
    provider: Mapped["SSOProvider"] = relationship(back_populates="sessions")


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    app_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sso_providers.id", ondelete="CASCADE"), nullable=False)
    scopes_granted: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status: Mapped[ConsentStatus] = mapped_column(Enum(ConsentStatus), nullable=False, default=ConsentStatus.active)

    user: Mapped["User"] = relationship(back_populates="consent_records")
    provider: Mapped["SSOProvider"] = relationship(back_populates="consents")
