"""
Biometric service with AI simulation.

Real production system would call a face-recognition / liveness-detection model.
Here we use deterministic hash-based simulation so results are reproducible per user.
"""
import uuid
import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.biometric import BiometricRecord, BiometricType, BiometricStatus, RiskLevel
from app.models.user import User
from app.utils.audit import write_audit_entry


def _simulate_scores(user_id: uuid.UUID, btype: BiometricType) -> tuple[float, float, BiometricStatus, RiskLevel]:
    """Deterministic AI simulation based on user_id hash."""
    seed = int(hashlib.md5(f"{user_id}{btype}".encode()).hexdigest(), 16)
    liveness = round(0.3 + (seed % 700) / 1000, 3)  # range 0.3–0.999
    spoof = round(max(0.0, 1.0 - liveness - 0.05 + (seed % 100) / 2000), 3)

    if liveness >= 0.85 and spoof <= 0.15:
        status = BiometricStatus.verified
        risk = RiskLevel.low
    elif liveness >= 0.60 and spoof <= 0.40:
        status = BiometricStatus.flagged
        risk = RiskLevel.high
    elif liveness < 0.50:
        status = BiometricStatus.failed
        risk = RiskLevel.high
    else:
        status = BiometricStatus.pending
        risk = RiskLevel.medium

    return liveness, spoof, status, risk


async def submit_biometric(
    db: AsyncSession, user: User, btype: BiometricType
) -> BiometricRecord:
    liveness, spoof, status, risk = _simulate_scores(user.id, btype)
    record = BiometricRecord(
        id=uuid.uuid4(),
        user_id=user.id,
        type=btype,
        status=status,
        liveness_score=liveness,
        spoof_probability=spoof,
        risk_level=risk,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    await write_audit_entry(
        db,
        action="Biometric Verification",
        actor_id=user.id,
        actor_name=user.name,
        target=user.name,
        details=f"{btype} verification — status: {status}, liveness: {liveness}",
    )
    return record


async def get_records(db: AsyncSession, user: User, is_admin: bool) -> list[BiometricRecord]:
    query = (
        select(BiometricRecord)
        .options(selectinload(BiometricRecord.user))
        .order_by(BiometricRecord.created_at.desc())
    )
    if not is_admin:
        query = query.where(BiometricRecord.user_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_record_by_id(db: AsyncSession, record_id: uuid.UUID) -> BiometricRecord | None:
    result = await db.execute(select(BiometricRecord).where(BiometricRecord.id == record_id))
    return result.scalar_one_or_none()


BIOMETRIC_MODEL_METRICS = {
    "accuracy": 0.964,
    "precision": 0.951,
    "recall": 0.978,
    "f1Score": 0.964,
    "falseAcceptRate": 0.003,
    "falseRejectRate": 0.022,
    "biasMetrics": {
        "genderGap": 0.012,
        "ageGroupGap": 0.018,
        "skinToneGap": 0.009,
    },
}
