"""
Card service: issuance, status management, transactions, and rule enforcement simulation.
"""
import uuid
import random
import string
from datetime import datetime, timezone, date

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import FinCard, CardTransaction, CardRule, CardStatus, TransactionStatus
from app.models.user import User
from app.schemas.card import CardCreate, CardStatusUpdate, CardTransactionCreate, CardRuleCreate, CardRuleUpdate
from app.utils.audit import write_audit_entry


def _mask_card_number() -> str:
    prefix = random.choice(["4532", "5421", "4916", "3742"])
    return f"{prefix} •••• •••• {random.randint(1000,9999)}"


def _generate_cvv() -> str:
    return "".join(random.choices(string.digits, k=3))


def _expires_at() -> str:
    today = date.today()
    return f"{today.year + 2}-{today.month:02d}"


def _apply_card_rules(card: FinCard, txn: CardTransaction) -> TransactionStatus:
    """Simulate rule engine: flag high-value transactions."""
    for rule in card.rules:
        if not rule.enabled:
            continue
        if "10,000" in rule.condition and txn.amount > 10000:
            if "biometric" in rule.action.lower():
                return TransactionStatus.flagged
        if "outside" in rule.condition.lower() and txn.location not in ("", "Online", "Addis Ababa"):
            return TransactionStatus.flagged
    return TransactionStatus.completed


async def get_cards(db: AsyncSession, user: User, is_admin: bool) -> list[FinCard]:
    query = select(FinCard).options(selectinload(FinCard.rules), selectinload(FinCard.linked_identity))
    if not is_admin:
        query = query.where(FinCard.user_id == user.id)
    result = await db.execute(query.order_by(FinCard.issued_at.desc()))
    return list(result.scalars().all())


async def get_card_by_id(db: AsyncSession, card_id: uuid.UUID) -> FinCard:
    result = await db.execute(
        select(FinCard)
        .options(selectinload(FinCard.rules), selectinload(FinCard.linked_identity))
        .where(FinCard.id == card_id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


async def create_card(db: AsyncSession, user: User, data: CardCreate) -> FinCard:
    card = FinCard(
        id=uuid.uuid4(),
        user_id=user.id,
        holder_name=user.name,
        card_number_masked=_mask_card_number(),
        card_type=data.card_type,
        status=CardStatus.active,
        expires_at=_expires_at(),
        daily_limit=data.daily_limit,
        monthly_limit=data.monthly_limit,
        current_spend=0.0,
        linked_identity_id=data.linked_identity_id,
        tokenized=True,
        dynamic_cvv=_generate_cvv(),
        issued_at=date.today().isoformat(),
        biometric_bound=data.biometric_bound,
    )
    db.add(card)
    await write_audit_entry(
        db,
        action="Card Issued",
        actor_id=user.id,
        actor_name=user.name,
        target=user.name,
        details=f"{data.card_type} card issued to {user.name}",
    )
    return card


async def update_card_status(db: AsyncSession, card_id: uuid.UUID, data: CardStatusUpdate, actor: User) -> FinCard:
    card = await get_card_by_id(db, card_id)
    old = card.status
    card.status = data.status
    await write_audit_entry(
        db,
        action=f"Card {data.status.capitalize()}",
        actor_id=actor.id,
        actor_name=actor.name,
        target=str(card.user_id),
        details=f"Card {card_id} status changed from {old} to {data.status}",
    )
    return card


# --- Transactions ---

async def get_transactions(db: AsyncSession, card_id: uuid.UUID) -> list[CardTransaction]:
    result = await db.execute(
        select(CardTransaction)
        .where(CardTransaction.card_id == card_id)
        .order_by(CardTransaction.timestamp.desc())
    )
    return list(result.scalars().all())


async def create_transaction(
    db: AsyncSession, card_id: uuid.UUID, data: CardTransactionCreate, actor: User
) -> CardTransaction:
    card = await get_card_by_id(db, card_id)
    if card.status != CardStatus.active:
        raise HTTPException(status_code=400, detail=f"Card is {card.status}, transactions not allowed")

    txn = CardTransaction(
        id=uuid.uuid4(),
        card_id=card_id,
        type=data.type,
        amount=data.amount,
        currency=data.currency,
        merchant=data.merchant,
        status=TransactionStatus.pending,
        timestamp=datetime.now(timezone.utc),
        location=data.location,
        offline=data.offline,
    )

    # Run rule engine simulation
    txn.status = _apply_card_rules(card, txn)

    if txn.status == TransactionStatus.completed and data.type in ("payment", "withdrawal"):
        card.current_spend += data.amount

    db.add(txn)
    await write_audit_entry(
        db,
        action="Transaction" + (" Flagged" if txn.status == TransactionStatus.flagged else " Processed"),
        actor_id=actor.id,
        actor_name=actor.name,
        target=data.merchant,
        details=f"{data.type} of {data.amount} {data.currency} at {data.merchant} — {txn.status}",
    )
    return txn


# --- Rules ---

async def get_rules(db: AsyncSession, card_id: uuid.UUID) -> list[CardRule]:
    result = await db.execute(select(CardRule).where(CardRule.card_id == card_id))
    return list(result.scalars().all())


async def create_rule(db: AsyncSession, card_id: uuid.UUID, data: CardRuleCreate) -> CardRule:
    rule = CardRule(
        id=uuid.uuid4(),
        card_id=card_id,
        rule_name=data.rule_name,
        condition=data.condition,
        action=data.action,
        enabled=data.enabled,
    )
    db.add(rule)
    return rule


async def update_rule(db: AsyncSession, card_id: uuid.UUID, rule_id: uuid.UUID, data: CardRuleUpdate) -> CardRule:
    result = await db.execute(
        select(CardRule).where(CardRule.id == rule_id, CardRule.card_id == card_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if data.enabled is not None:
        rule.enabled = data.enabled
    if data.rule_name is not None:
        rule.rule_name = data.rule_name
    if data.condition is not None:
        rule.condition = data.condition
    if data.action is not None:
        rule.action = data.action
    return rule
