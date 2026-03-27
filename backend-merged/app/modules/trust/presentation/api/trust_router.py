"""
Trust router � trust scoring and risk evaluation.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.api.dependencies import DBSession, CurrentUserId
from app.modules.trust.infrastructure.persistence.trust_repository_impl import SQLAlchemyTrustRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.digital_identity.infrastructure.persistence.identity_repository_impl import SQLAlchemyDigitalIdentityRepository
from app.modules.trust.application.use_cases.calculate_trust_score import CalculateTrustScoreUseCase

router = APIRouter()


class TrustProfileResponse(BaseModel):
    user_id: str
    trust_score: float
    risk_level: str
    email_verified: bool
    phone_verified: bool
    kyc_tier: int
    face_verified: bool
    voice_verified: bool
    digital_identity_active: bool
    account_age_days: int
    last_calculated_at: str


@router.get("/profile", response_model=TrustProfileResponse)
async def get_trust_profile(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Get current user's trust profile.
    
    Returns trust score, risk level, and contributing factors.
    """
    trust_repo = SQLAlchemyTrustRepository(session)
    profile = await trust_repo.get_by_user_id(current_user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Trust profile not found")
    
    return TrustProfileResponse(
        user_id=profile.user_id,
        trust_score=float(profile.trust_score),
        risk_level=profile.risk_level,
        email_verified=profile.email_verified,
        phone_verified=profile.phone_verified,
        kyc_tier=profile.kyc_tier,
        face_verified=profile.face_verified,
        voice_verified=profile.voice_verified,
        digital_identity_active=profile.digital_identity_active,
        account_age_days=profile.account_age_days,
        last_calculated_at=profile.last_calculated_at.isoformat(),
    )


@router.post("/evaluate", response_model=TrustProfileResponse)
async def evaluate_trust(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Recalculate trust score for current user.
    
    Triggers fresh calculation based on current verification status.
    """
    trust_repo = SQLAlchemyTrustRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    kyc_repo = SQLAlchemyKYCRepository(session)
    biometric_repo = SQLAlchemyBiometricRepository(session)
    identity_repo = SQLAlchemyDigitalIdentityRepository(session)
    
    use_case = CalculateTrustScoreUseCase(
        trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
    )
    
    profile = await use_case.execute(current_user_id)
    
    await session.commit()
    
    return TrustProfileResponse(
        user_id=profile.user_id,
        trust_score=float(profile.trust_score),
        risk_level=profile.risk_level,
        email_verified=profile.email_verified,
        phone_verified=profile.phone_verified,
        kyc_tier=profile.kyc_tier,
        face_verified=profile.face_verified,
        voice_verified=profile.voice_verified,
        digital_identity_active=profile.digital_identity_active,
        account_age_days=profile.account_age_days,
        last_calculated_at=profile.last_calculated_at.isoformat(),
    )


@router.get("/profile/{user_id}", response_model=TrustProfileResponse)
async def get_user_trust_profile(
    user_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Get trust profile for specific user.
    
    Available to all authenticated users (for transparency).
    """
    trust_repo = SQLAlchemyTrustRepository(session)
    profile = await trust_repo.get_by_user_id(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Trust profile not found")
    
    return TrustProfileResponse(
        user_id=profile.user_id,
        trust_score=float(profile.trust_score),
        risk_level=profile.risk_level,
        email_verified=profile.email_verified,
        phone_verified=profile.phone_verified,
        kyc_tier=profile.kyc_tier,
        face_verified=profile.face_verified,
        voice_verified=profile.voice_verified,
        digital_identity_active=profile.digital_identity_active,
        account_age_days=profile.account_age_days,
        last_calculated_at=profile.last_calculated_at.isoformat(),
    )
