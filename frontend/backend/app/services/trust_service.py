"""
Trust scoring engine.

Score breakdown (0–100):
  +20  email verified
  +15  phone verified
  +25  KYC approved (tier 2)
  +20  biometric verified (tier 3)
  +10  active digital identity
  −20  flagged biometric
  −30  rejected KYC
  −15  flagged KYC
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trust import TrustProfile
from app.models.user import User
from app.models.kyc import KYCApplication, KYCStatus
from app.models.biometric import BiometricRecord, BiometricStatus
from app.models.identity import DigitalIdentity, IdentityStatus


async def evaluate_trust(db: AsyncSession, user: User) -> TrustProfile:
    """Recompute and persist trust profile for a user."""
    factors: dict = {}
    score = 0.0

    # Email / phone
    factors["email_verified"] = user.email_verified
    factors["phone_verified"] = user.phone_verified
    if user.email_verified:
        score += 20
    if user.phone_verified:
        score += 15

    # KYC
    kyc_result = await db.execute(
        select(KYCApplication)
        .where(KYCApplication.user_id == user.id)
        .order_by(KYCApplication.submitted_at.desc())
        .limit(1)
    )
    kyc = kyc_result.scalar_one_or_none()
    factors["kyc_status"] = kyc.status if kyc else None
    if kyc:
        if kyc.status == KYCStatus.approved:
            score += 25
        elif kyc.status == KYCStatus.rejected:
            score -= 30
        elif kyc.status == KYCStatus.flagged:
            score -= 15

    # Biometric
    bio_result = await db.execute(
        select(BiometricRecord)
        .where(BiometricRecord.user_id == user.id)
        .order_by(BiometricRecord.created_at.desc())
        .limit(1)
    )
    bio = bio_result.scalar_one_or_none()
    factors["biometric_status"] = bio.status if bio else None
    if bio:
        if bio.status == BiometricStatus.verified:
            score += 20
        elif bio.status == BiometricStatus.flagged:
            score -= 20

    # Digital identity
    did_result = await db.execute(
        select(DigitalIdentity)
        .where(DigitalIdentity.user_id == user.id, DigitalIdentity.status == IdentityStatus.active)
        .limit(1)
    )
    has_active_identity = did_result.scalar_one_or_none() is not None
    factors["active_identity"] = has_active_identity
    if has_active_identity:
        score += 10

    # Clamp to 0–100
    score = max(0.0, min(100.0, score))
    factors["computed_score"] = score

    # KYC tier
    kyc_tier = 0
    if user.email_verified or user.phone_verified:
        kyc_tier = 1
    if kyc and kyc.status == KYCStatus.approved:
        kyc_tier = 2
    if kyc_tier == 2 and bio and bio.status == BiometricStatus.verified:
        kyc_tier = 3

    # Risk level
    if score >= 70:
        risk_level = "low"
    elif score >= 40:
        risk_level = "medium"
    else:
        risk_level = "high"

    # Upsert trust profile
    existing = await db.execute(select(TrustProfile).where(TrustProfile.user_id == user.id))
    profile = existing.scalar_one_or_none()
    if profile:
        profile.trust_score = score
        profile.kyc_tier = kyc_tier
        profile.factors = factors
        profile.last_evaluated = datetime.now(timezone.utc)
    else:
        profile = TrustProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            trust_score=score,
            kyc_tier=kyc_tier,
            factors=factors,
            last_evaluated=datetime.now(timezone.utc),
        )
        db.add(profile)

    await db.flush()
    return profile


async def get_trust_profile(db: AsyncSession, user: User) -> TrustProfile:
    """Return existing profile or compute fresh."""
    result = await db.execute(select(TrustProfile).where(TrustProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = await evaluate_trust(db, user)
    return profile
