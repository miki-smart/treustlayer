"""
Trust router — trust scoring and risk evaluation.
"""
from fastapi import APIRouter, HTTPException

from app.api.dependencies import DBSession, CurrentUserId, CurrentUserRole
from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.digital_identity.infrastructure.persistence.identity_repository_impl import SQLAlchemyDigitalIdentityRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.trust.application.use_cases.recalculate_trust_for_user import RecalculateTrustForUserUseCase
from app.modules.trust.infrastructure.persistence.trust_repository_impl import SQLAlchemyTrustRepository
from app.modules.trust.presentation.helpers.trust_profile_response import build_trust_profile_response
from app.modules.trust.presentation.schemas.trust_schemas import TrustProfileResponse

router = APIRouter()


def _repos(session):
    return (
        SQLAlchemyTrustRepository(session),
        SQLAlchemyUserRepository(session),
        SQLAlchemyKYCRepository(session),
        SQLAlchemyBiometricRepository(session),
        SQLAlchemyDigitalIdentityRepository(session),
    )


@router.get("/profile", response_model=TrustProfileResponse)
async def get_trust_profile(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Get current user's trust profile.

    If no stored profile exists yet, computes and persists one (same as POST /evaluate).
    """
    trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo = _repos(session)
    user = await user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await trust_repo.get_by_user_id(current_user_id)
    if not profile:
        recalc = RecalculateTrustForUserUseCase(
            trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
        )
        profile = await recalc.execute(current_user_id)
        await session.commit()

    return build_trust_profile_response(profile, user)


@router.post("/evaluate", response_model=TrustProfileResponse)
async def evaluate_trust(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Recalculate trust score for current user.

    Triggers fresh calculation based on current verification status.
    """
    trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo = _repos(session)
    user = await user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recalc = RecalculateTrustForUserUseCase(
        trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
    )
    profile = await recalc.execute(current_user_id)

    await session.commit()

    return build_trust_profile_response(profile, user)


@router.get("/profile/{user_id}", response_model=TrustProfileResponse)
async def get_user_trust_profile(
    user_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
    role: CurrentUserRole,
):
    """
    Get trust profile for a specific user.

    If the row is missing, it is computed for the current user, or for admins / KYC approvers viewing another user.
    """
    if user_id != current_user_id and role not in ("admin", "kyc_approver"):
        raise HTTPException(status_code=403, detail="Forbidden")

    trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo = _repos(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await trust_repo.get_by_user_id(user_id)
    if not profile:
        recalc = RecalculateTrustForUserUseCase(
            trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
        )
        profile = await recalc.execute(user_id)
        await session.commit()

    return build_trust_profile_response(profile, user)
