"""
CalculateTrustScoreUseCase — enhanced trust scoring with biometrics and DID.
"""
import logging
from datetime import datetime, timezone

from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.trust.domain.repositories.trust_repository import TrustRepository
from app.modules.identity.domain.repositories.user_repository import UserRepository
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository
from app.modules.biometric.domain.repositories.biometric_repository import BiometricRepository
from app.modules.digital_identity.domain.repositories.identity_repository import DigitalIdentityRepository
from app.modules.biometric.domain.entities.biometric_record import BiometricType, BiometricStatus
from app.modules.digital_identity.domain.entities.digital_identity import IdentityStatus

logger = logging.getLogger(__name__)


class CalculateTrustScoreUseCase:
    def __init__(
        self,
        trust_repo: TrustRepository,
        user_repo: UserRepository,
        kyc_repo: KYCRepository,
        biometric_repo: BiometricRepository,
        identity_repo: DigitalIdentityRepository,
    ):
        self.trust_repo = trust_repo
        self.user_repo = user_repo
        self.kyc_repo = kyc_repo
        self.biometric_repo = biometric_repo
        self.identity_repo = identity_repo

    async def execute(self, user_id: str) -> TrustProfile:
        """
        Calculate trust score for user.
        
        Enhanced algorithm:
        - Email verified: +20
        - Phone verified: +15
        - KYC tier: +0/+15/+25/+35
        - Face biometric verified: +10 (NEW)
        - Voice biometric verified: +5 (NEW)
        - Digital identity active: +5 (NEW)
        - Account age: +0 to +10
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        kyc = await self.kyc_repo.get_by_user_id(user_id)
        kyc_tier = 0
        if kyc:
            tier_map = {"tier_0": 0, "tier_1": 1, "tier_2": 2, "tier_3": 3}
            kyc_tier = tier_map.get(kyc.tier.value, 0)
        
        face_records = await self.biometric_repo.list_by_user_and_type(user_id, BiometricType.FACE)
        face_verified = any(r.status == BiometricStatus.VERIFIED for r in face_records)
        
        voice_records = await self.biometric_repo.list_by_user_and_type(user_id, BiometricType.VOICE)
        voice_verified = any(r.status == BiometricStatus.VERIFIED for r in voice_records)
        
        digital_identity = await self.identity_repo.get_by_user_id(user_id)
        # Must be bool: `None and ...` yields None and breaks NOT NULL on trust.profiles.digital_identity_active
        digital_identity_active = (
            digital_identity is not None and digital_identity.status == IdentityStatus.ACTIVE
        )
        
        account_age_days = (datetime.now(timezone.utc) - user.created_at).days
        
        profile = await self.trust_repo.get_by_user_id(user_id)
        if not profile:
            profile = TrustProfile(user_id=user_id)
        
        profile.update_score(
            email_verified=user.is_email_verified,
            phone_verified=user.phone_verified,
            kyc_tier=kyc_tier,
            face_verified=face_verified,
            voice_verified=voice_verified,
            digital_identity_active=digital_identity_active,
            account_age_days=account_age_days,
        )
        
        if await self.trust_repo.get_by_user_id(user_id):
            saved = await self.trust_repo.update(profile)
        else:
            saved = await self.trust_repo.create(profile)
        
        logger.info(f"Trust score calculated for user {user_id}: {saved.trust_score:.2f}")
        
        return saved
