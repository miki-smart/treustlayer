import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.card import CardStatus, CardType, TransactionType, TransactionStatus


class FinCardOut(BaseModel):
    id: uuid.UUID
    userId: str
    holderName: str
    cardNumber: str
    cardType: CardType
    status: CardStatus
    expiresAt: str
    dailyLimit: float
    monthlyLimit: float
    currentSpend: float
    linkedIdentity: str | None = None
    tokenized: bool
    dynamicCVV: str
    issuedAt: str
    biometricBound: bool

    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    card_type: CardType = CardType.virtual
    daily_limit: float = 50000.0
    monthly_limit: float = 500000.0
    biometric_bound: bool = False
    linked_identity_id: uuid.UUID | None = None


class CardStatusUpdate(BaseModel):
    status: CardStatus


class CardTransactionOut(BaseModel):
    id: uuid.UUID
    cardId: str
    type: TransactionType
    amount: float
    currency: str
    merchant: str
    status: TransactionStatus
    timestamp: str
    location: str
    offline: bool

    model_config = {"from_attributes": True}


class CardTransactionCreate(BaseModel):
    type: TransactionType
    amount: float
    currency: str = "ETB"
    merchant: str
    location: str = ""
    offline: bool = False


class CardRuleOut(BaseModel):
    id: uuid.UUID
    cardId: str
    ruleName: str
    condition: str
    action: str
    enabled: bool

    model_config = {"from_attributes": True}


class CardRuleCreate(BaseModel):
    rule_name: str
    condition: str
    action: str
    enabled: bool = True


class CardRuleUpdate(BaseModel):
    enabled: bool | None = None
    rule_name: str | None = None
    condition: str | None = None
    action: str | None = None
