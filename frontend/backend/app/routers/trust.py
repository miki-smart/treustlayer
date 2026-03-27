"""
Trust & Risk endpoints.

  GET  /trust/profile           — current user's trust profile
  POST /trust/evaluate          — force re-evaluation (current user)
  GET  /trust/profile/{user_id} — admin: fetch any user's trust profile
"""
import uuid
from fastapi import HTTPException
from app.dependencies import CurrentUser, AdminUser, DB
from app.models.user import UserRole, User
from app.schemas.trust import TrustProfileOut
from app.services import trust_service
from sqlalchemy import select
from fastapi import APIRouter

router = APIRouter(prefix="/trust", tags=["Trust & Risk"])


def _profile_to_out(profile, user_id: str) -> TrustProfileOut:
    score = profile.trust_score
    risk = "low" if score >= 70 else ("medium" if score >= 40 else "high")
    return TrustProfileOut(
        userId=user_id,
        trustScore=score,
        kycTier=profile.kyc_tier,
        riskLevel=risk,
        factors=profile.factors,
        lastEvaluated=profile.last_evaluated.isoformat() if profile.last_evaluated else "",
    )


@router.get("/profile", response_model=TrustProfileOut, summary="My trust profile")
async def my_trust_profile(current_user: CurrentUser, db: DB):
    profile = await trust_service.get_trust_profile(db, current_user)
    return _profile_to_out(profile, str(current_user.id))


@router.post("/evaluate", response_model=TrustProfileOut, summary="Force trust re-evaluation")
async def evaluate_trust(current_user: CurrentUser, db: DB):
    """Triggers a fresh trust score computation based on current KYC/biometric state."""
    profile = await trust_service.evaluate_trust(db, current_user)
    return _profile_to_out(profile, str(current_user.id))


@router.get("/profile/{user_id}", response_model=TrustProfileOut, summary="Get user trust profile (admin)")
async def get_user_trust_profile(user_id: uuid.UUID, current_user: AdminUser, db: DB):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = await trust_service.get_trust_profile(db, user)
    return _profile_to_out(profile, str(user.id))
