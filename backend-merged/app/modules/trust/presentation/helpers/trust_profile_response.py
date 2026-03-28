"""Map TrustProfile + User domain entities to API response."""
from datetime import datetime, timezone

from app.modules.auth.application.trust_risk import risk_level_and_flag
from app.modules.identity.domain.entities.user import User
from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.trust.presentation.schemas.trust_schemas import TrustProfileResponse


def build_trust_profile_response(profile: TrustProfile, user: User) -> TrustProfileResponse:
    risk_level, _ = risk_level_and_flag(profile.trust_score)
    now = datetime.now(timezone.utc)
    created = user.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    account_age_days = max(0, (now - created).days)
    return TrustProfileResponse(
        user_id=profile.user_id,
        trust_score=float(profile.trust_score),
        risk_level=risk_level,
        email_verified=user.is_email_verified,
        phone_verified=user.phone_verified,
        kyc_tier=profile.kyc_tier,
        face_verified=profile.face_verified,
        voice_verified=profile.voice_verified,
        digital_identity_active=profile.digital_identity_active,
        account_age_days=account_age_days,
        last_calculated_at=profile.last_evaluated.isoformat(),
    )
