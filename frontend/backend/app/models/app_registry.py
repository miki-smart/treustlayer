import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import enum


class AppStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"


class AppCategory(str, enum.Enum):
    banking = "banking"
    lending = "lending"
    payments = "payments"
    insurance = "insurance"
    investment = "investment"
    wallet = "wallet"
    other = "other"


class RegisteredApp(Base):
    __tablename__ = "registered_apps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    client_secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[AppCategory] = mapped_column(Enum(AppCategory), nullable=False, default=AppCategory.other)
    status: Mapped[AppStatus] = mapped_column(Enum(AppStatus), nullable=False, default=AppStatus.pending)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    allowed_scopes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    redirect_uris: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # api_key for non-OIDC integrations (rotatable)
    api_key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    @property
    def is_approved(self) -> bool:
        return self.status == AppStatus.approved

    @property
    def is_active(self) -> bool:
        return self.status != AppStatus.suspended

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    approved_by: Mapped["User | None"] = relationship(foreign_keys=[approved_by_id])
    auth_codes: Mapped[list["AuthorizationCode"]] = relationship(back_populates="app", cascade="all, delete-orphan")
    user_connections: Mapped[list["UserApp"]] = relationship(back_populates="app", cascade="all, delete-orphan")
    webhook_endpoints: Mapped[list["WebhookEndpoint"]] = relationship(back_populates="app", cascade="all, delete-orphan")


class AuthorizationCode(Base):
    __tablename__ = "authorization_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("registered_apps.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scopes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    code_challenge: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code_challenge_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    app: Mapped["RegisteredApp"] = relationship(back_populates="auth_codes")
    user: Mapped["User"] = relationship()


class UserApp(Base):
    """Tracks which apps a user has connected/authorized."""
    __tablename__ = "user_apps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    app_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("registered_apps.id", ondelete="CASCADE"), nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship()
    app: Mapped["RegisteredApp"] = relationship(back_populates="user_connections")
