import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Enum, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class CardStatus(str, enum.Enum):
    active = "active"
    frozen = "frozen"
    pending = "pending"
    expired = "expired"
    revoked = "revoked"


class CardType(str, enum.Enum):
    virtual = "virtual"
    physical = "physical"
    biometric = "biometric"


class TransactionType(str, enum.Enum):
    payment = "payment"
    withdrawal = "withdrawal"
    transfer = "transfer"
    refund = "refund"


class TransactionStatus(str, enum.Enum):
    completed = "completed"
    pending = "pending"
    failed = "failed"
    flagged = "flagged"


class FinCard(Base):
    __tablename__ = "fin_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    holder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    card_number_masked: Mapped[str] = mapped_column(String(25), nullable=False)
    card_type: Mapped[CardType] = mapped_column(Enum(CardType), nullable=False, default=CardType.virtual)
    status: Mapped[CardStatus] = mapped_column(Enum(CardStatus), nullable=False, default=CardStatus.pending)
    expires_at: Mapped[str] = mapped_column(String(10), nullable=False)
    daily_limit: Mapped[float] = mapped_column(Float, nullable=False, default=50000.0)
    monthly_limit: Mapped[float] = mapped_column(Float, nullable=False, default=500000.0)
    current_spend: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    linked_identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("digital_identities.id", ondelete="SET NULL"), nullable=True)
    tokenized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    dynamic_cvv: Mapped[str] = mapped_column(String(10), nullable=False, default="---")
    issued_at: Mapped[str] = mapped_column(String(20), nullable=False)
    biometric_bound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="fin_cards")
    linked_identity: Mapped["DigitalIdentity | None"] = relationship(back_populates="fin_cards")
    transactions: Mapped[list["CardTransaction"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    rules: Mapped[list["CardRule"]] = relationship(back_populates="card", cascade="all, delete-orphan")


class CardTransaction(Base):
    __tablename__ = "card_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fin_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="ETB")
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.pending)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    offline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    card: Mapped["FinCard"] = relationship(back_populates="transactions")


class CardRule(Base):
    __tablename__ = "card_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fin_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    card: Mapped["FinCard"] = relationship(back_populates="rules")
