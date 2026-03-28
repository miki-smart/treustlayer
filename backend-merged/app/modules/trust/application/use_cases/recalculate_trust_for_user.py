"""
RecalculateTrustForUserUseCase — single entry point for trust score refresh after side effects (e.g. biometrics).
"""
from app.modules.biometric.domain.repositories.biometric_repository import BiometricRepository
from app.modules.digital_identity.domain.repositories.identity_repository import DigitalIdentityRepository
from app.modules.identity.domain.repositories.user_repository import UserRepository
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository
from app.modules.trust.application.use_cases.calculate_trust_score import CalculateTrustScoreUseCase
from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.trust.domain.repositories.trust_repository import TrustRepository


class RecalculateTrustForUserUseCase:
    """Delegates to CalculateTrustScoreUseCase to avoid duplicating scoring logic."""

    def __init__(
        self,
        trust_repo: TrustRepository,
        user_repo: UserRepository,
        kyc_repo: KYCRepository,
        biometric_repo: BiometricRepository,
        identity_repo: DigitalIdentityRepository,
    ):
        self._inner = CalculateTrustScoreUseCase(
            trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
        )

    async def execute(self, user_id: str) -> TrustProfile:
        return await self._inner.execute(user_id)
