"""
Trust router — trust scoring and risk evaluation.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import DBSession, CurrentUserId

router = APIRouter()


class TrustProfile(BaseModel):
    trust_score: float
    kyc_tier: int
    risk_level: str
    factors: dict


@router.get("/profile", response_model=TrustProfile)
async def get_trust_profile(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Get trust profile. Stub implementation."""
    return TrustProfile(
        trust_score=0.0,
        kyc_tier=0,
        risk_level="high",
        factors={},
    )


@router.post("/evaluate", response_model=TrustProfile)
async def evaluate_trust(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Evaluate trust score. Stub implementation."""
    return TrustProfile(
        trust_score=0.0,
        kyc_tier=0,
        risk_level="high",
        factors={},
    )
