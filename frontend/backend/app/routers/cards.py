import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUser, AdminUser, DB
from app.schemas.card import (
    FinCardOut, CardCreate, CardStatusUpdate,
    CardTransactionOut, CardTransactionCreate,
    CardRuleOut, CardRuleCreate, CardRuleUpdate,
)
from app.services import card_service
from app.models.user import UserRole


router = APIRouter(prefix="/cards", tags=["Cards"])


def _card_to_out(card) -> FinCardOut:
    linked = card.linked_identity.unique_id if card.linked_identity else None
    return FinCardOut(
        id=card.id,
        userId=str(card.user_id),
        holderName=card.holder_name,
        cardNumber=card.card_number_masked,
        cardType=card.card_type,
        status=card.status,
        expiresAt=card.expires_at,
        dailyLimit=card.daily_limit,
        monthlyLimit=card.monthly_limit,
        currentSpend=card.current_spend,
        linkedIdentity=linked,
        tokenized=card.tokenized,
        dynamicCVV=card.dynamic_cvv,
        issuedAt=card.issued_at,
        biometricBound=card.biometric_bound,
    )


def _txn_to_out(txn) -> CardTransactionOut:
    return CardTransactionOut(
        id=txn.id,
        cardId=str(txn.card_id),
        type=txn.type,
        amount=txn.amount,
        currency=txn.currency,
        merchant=txn.merchant,
        status=txn.status,
        timestamp=txn.timestamp.isoformat(),
        location=txn.location,
        offline=txn.offline,
    )


def _rule_to_out(rule) -> CardRuleOut:
    return CardRuleOut(
        id=rule.id,
        cardId=str(rule.card_id),
        ruleName=rule.rule_name,
        condition=rule.condition,
        action=rule.action,
        enabled=rule.enabled,
    )


@router.get("/", response_model=list[FinCardOut])
async def list_cards(current_user: CurrentUser, db: DB):
    is_admin = current_user.role == UserRole.admin
    cards = await card_service.get_cards(db, current_user, is_admin)
    return [_card_to_out(c) for c in cards]


@router.post("/", response_model=FinCardOut, status_code=201)
async def create_card(body: CardCreate, current_user: CurrentUser, db: DB):
    card = await card_service.create_card(db, current_user, body)
    return _card_to_out(card)


@router.get("/{card_id}", response_model=FinCardOut)
async def get_card(card_id: uuid.UUID, current_user: CurrentUser, db: DB):
    card = await card_service.get_card_by_id(db, card_id)
    if current_user.role != UserRole.admin and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _card_to_out(card)


@router.patch("/{card_id}/status", response_model=FinCardOut)
async def update_card_status(card_id: uuid.UUID, body: CardStatusUpdate, current_user: CurrentUser, db: DB):
    if current_user.role != UserRole.admin:
        card = await card_service.get_card_by_id(db, card_id)
        if card.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    card = await card_service.update_card_status(db, card_id, body, current_user)
    return _card_to_out(card)


# --- Transactions ---

@router.get("/{card_id}/transactions", response_model=list[CardTransactionOut])
async def list_transactions(card_id: uuid.UUID, current_user: CurrentUser, db: DB):
    card = await card_service.get_card_by_id(db, card_id)
    if current_user.role != UserRole.admin and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    txns = await card_service.get_transactions(db, card_id)
    return [_txn_to_out(t) for t in txns]


@router.post("/{card_id}/transactions", response_model=CardTransactionOut, status_code=201)
async def create_transaction(card_id: uuid.UUID, body: CardTransactionCreate, current_user: CurrentUser, db: DB):
    txn = await card_service.create_transaction(db, card_id, body, current_user)
    return _txn_to_out(txn)


# --- Rules ---

@router.get("/{card_id}/rules", response_model=list[CardRuleOut])
async def list_rules(card_id: uuid.UUID, current_user: CurrentUser, db: DB):
    card = await card_service.get_card_by_id(db, card_id)
    if current_user.role != UserRole.admin and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    rules = await card_service.get_rules(db, card_id)
    return [_rule_to_out(r) for r in rules]


@router.post("/{card_id}/rules", response_model=CardRuleOut, status_code=201)
async def create_rule(card_id: uuid.UUID, body: CardRuleCreate, current_user: CurrentUser, db: DB):
    card = await card_service.get_card_by_id(db, card_id)
    if current_user.role != UserRole.admin and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    rule = await card_service.create_rule(db, card_id, body)
    return _rule_to_out(rule)


@router.put("/{card_id}/rules/{rule_id}", response_model=CardRuleOut)
async def update_rule(card_id: uuid.UUID, rule_id: uuid.UUID, body: CardRuleUpdate, current_user: CurrentUser, db: DB):
    card = await card_service.get_card_by_id(db, card_id)
    if current_user.role != UserRole.admin and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    rule = await card_service.update_rule(db, card_id, rule_id, body)
    return _rule_to_out(rule)
