import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    kyc_approver = "kyc_approver"
    app_owner = "app_owner"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # username: unique login handle — falls back to email prefix if not set
    username: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.user)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Convenience helpers
    @property
    def full_name(self) -> str:
        return self.name

    @property
    def phone_number(self) -> str | None:
        return self.phone

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified

    @property
    def effective_username(self) -> str:
        return self.username or self.email.split("@")[0]

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    biometric_records: Mapped[list["BiometricRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    kyc_applications: Mapped[list["KYCApplication"]] = relationship(foreign_keys="KYCApplication.user_id", back_populates="user", cascade="all, delete-orphan")
    digital_identities: Mapped[list["DigitalIdentity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sso_sessions: Mapped[list["SSOSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    consent_records: Mapped[list["ConsentRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    fin_cards: Mapped[list["FinCard"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_entries: Mapped[list["AuditEntry"]] = relationship(back_populates="actor", cascade="all, delete-orphan")
    consent_grants: Mapped[list["ConsentGrant"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    # OIDC session metadata
    client_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
