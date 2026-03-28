"""Shared wiring for trust recalculation from other modules (e.g. biometrics)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.digital_identity.infrastructure.persistence.identity_repository_impl import SQLAlchemyDigitalIdentityRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.trust.application.use_cases.recalculate_trust_for_user import RecalculateTrustForUserUseCase
from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.trust.infrastructure.persistence.trust_repository_impl import SQLAlchemyTrustRepository


async def recalculate_trust_for_user_session(session: AsyncSession, user_id: str) -> TrustProfile:
    """Run full trust score calculation and persist; caller commits the session."""
    trust_repo = SQLAlchemyTrustRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    kyc_repo = SQLAlchemyKYCRepository(session)
    biometric_repo = SQLAlchemyBiometricRepository(session)
    identity_repo = SQLAlchemyDigitalIdentityRepository(session)
    uc = RecalculateTrustForUserUseCase(
        trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
    )
    return await uc.execute(user_id)
