"""
GetUserInfoUseCase — OIDC UserInfo endpoint logic.
"""
import logging
from typing import Any, Dict

from app.core.exceptions import NotFoundError
from app.modules.biometric.domain.entities.biometric_record import (
    BiometricStatus,
    BiometricType,
)
from app.modules.biometric.domain.repositories.biometric_repository import (
    BiometricRepository,
)
from app.modules.digital_identity.domain.repositories.identity_repository import (
    DigitalIdentityRepository,
)
from app.modules.identity.domain.repositories.user_repository import UserRepository
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository
from app.modules.trust.domain.repositories.trust_repository import TrustRepository

logger = logging.getLogger(__name__)


class GetUserInfoUseCase:
    """
    OIDC UserInfo endpoint.
    
    Returns user claims based on granted scopes.
    """
    
    def __init__(
        self,
        user_repo: UserRepository,
        kyc_repo: KYCRepository,
        trust_repo: TrustRepository,
        biometric_repo: BiometricRepository,
        identity_repo: DigitalIdentityRepository,
    ):
        self.user_repo = user_repo
        self.kyc_repo = kyc_repo
        self.trust_repo = trust_repo
        self.biometric_repo = biometric_repo
        self.identity_repo = identity_repo
    
    async def execute(self, user_id: str) -> Dict[str, Any]:
        """
        Get user info claims.
        
        Args:
            user_id: User ID from JWT
        
        Returns:
            Dict with user claims
        
        Raises:
            NotFoundError: User not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Base claims (always included)
        claims = {
            "sub": user.id,
            "email": user.email,
            "email_verified": user.is_email_verified,
            "preferred_username": user.username,
            "name": user.full_name or user.username,
            "phone_number": user.phone_number,
            "phone_number_verified": user.phone_verified,
            "picture": user.avatar,
            "updated_at": int(user.updated_at.timestamp()),
        }
        
        # KYC claims
        kyc = await self.kyc_repo.get_by_user_id(user.id)
        if kyc:
            claims["kyc_tier"] = kyc.tier.value
            claims["kyc_status"] = kyc.status.value
        
        # Trust claims
        trust = await self.trust_repo.get_by_user_id(user.id)
        if trust:
            claims["trust_score"] = float(trust.trust_score)
            claims["risk_level"] = trust.risk_level
        
        # Biometric claims
        face_records = await self.biometric_repo.list_by_user_and_type(
            user.id, BiometricType.FACE
        )
        voice_records = await self.biometric_repo.list_by_user_and_type(
            user.id, BiometricType.VOICE
        )
        claims["face_verified"] = any(
            r.status == BiometricStatus.VERIFIED for r in face_records
        )
        claims["voice_verified"] = any(
            r.status == BiometricStatus.VERIFIED for r in voice_records
        )
        claims["biometric_verified"] = claims["face_verified"] or claims["voice_verified"]
        
        # Digital identity claims
        digital_identity = await self.identity_repo.get_by_user_id(user.id)
        if digital_identity:
            claims["digital_identity_id"] = digital_identity.identity_id
            claims["identity_status"] = digital_identity.status.value
        
        logger.info(f"UserInfo retrieved for user {user_id}")
        
        return claims
