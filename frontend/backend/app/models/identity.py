import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class IdentityStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    revoked = "revoked"
    pending = "pending"


class DigitalIdentity(Base):
    __tablename__ = "digital_identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    unique_id: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    status: Mapped[IdentityStatus] = mapped_column(Enum(IdentityStatus), nullable=False, default=IdentityStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_verified: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="digital_identities")
    attributes: Mapped[list["IdentityAttribute"]] = relationship(back_populates="identity", cascade="all, delete-orphan")
    credentials: Mapped[list["IdentityCredential"]] = relationship(back_populates="identity", cascade="all, delete-orphan")
    fin_cards: Mapped[list["FinCard"]] = relationship(back_populates="linked_identity")


class IdentityAttribute(Base):
    __tablename__ = "identity_attributes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("digital_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    identity: Mapped["DigitalIdentity"] = relationship(back_populates="attributes")


class IdentityCredential(Base):
    __tablename__ = "identity_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("digital_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    identity: Mapped["DigitalIdentity"] = relationship(back_populates="credentials")
