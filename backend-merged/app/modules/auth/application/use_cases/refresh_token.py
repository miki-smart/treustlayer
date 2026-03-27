"""
RefreshTokenUseCase — refresh access token using refresh token.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, hash_secret
from app.modules.auth.domain.repositories.auth_repository import AuthRepository
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


class RefreshTokenUseCase:
    """
    Refresh access token using refresh token.
    """
    
    def __init__(
        self,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
        kyc_repo: KYCRepository,
        trust_repo: TrustRepository,
        biometric_repo: BiometricRepository,
        identity_repo: DigitalIdentityRepository,
    ):
        self.auth_repo = auth_repo
        self.user_repo = user_repo
        self.kyc_repo = kyc_repo
        self.trust_repo = trust_repo
        self.biometric_repo = biometric_repo
        self.identity_repo = identity_repo
    
    async def execute(
        self, refresh_token_value: str, client_id: str, client_secret: str
    ) -> Dict[str, Any]:
        """
        Refresh access token.
        
        Args:
            refresh_token_value: Refresh token value
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
        
        Returns:
            Dict with new access_token and token_type
        
        Raises:
            UnauthorizedError: Invalid or expired refresh token
        """
        # 1. Hash and retrieve refresh token
        token_hash = hash_secret(refresh_token_value)
        refresh_token = await self.auth_repo.get_refresh_token(token_hash)
        
        if not refresh_token:
            logger.warning("Invalid refresh token attempted")
            raise UnauthorizedError("Invalid refresh token")
        
        # 2. Verify token is valid
        if not refresh_token.is_valid():
            logger.warning(f"Expired or revoked refresh token: {refresh_token.id}")
            raise UnauthorizedError("Refresh token expired or revoked")
        
        # 3. Verify client_id matches
        if refresh_token.client_id != client_id:
            logger.warning(f"Client ID mismatch for refresh token: {refresh_token.id}")
            raise UnauthorizedError("Client ID mismatch")
        
        # 4. Update last used timestamp
        refresh_token.update_last_used()
        await self.auth_repo.save_refresh_token(refresh_token)
        
        # 5. Load user and related data for fresh claims
        user = await self.user_repo.get_by_id(refresh_token.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        
        kyc = await self.kyc_repo.get_by_user_id(user.id)
        trust = await self.trust_repo.get_by_user_id(user.id)
        
        face_records = await self.biometric_repo.list_by_user_and_type(
            user.id, BiometricType.FACE
        )
        voice_records = await self.biometric_repo.list_by_user_and_type(
            user.id, BiometricType.VOICE
        )
        face_verified = any(r.status == BiometricStatus.VERIFIED for r in face_records)
        voice_verified = any(r.status == BiometricStatus.VERIFIED for r in voice_records)
        
        digital_identity = await self.identity_repo.get_by_user_id(user.id)
        
        # 6. Generate new access token with updated claims
        extra_claims = {
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "email_verified": user.is_email_verified,
            "phone_verified": user.phone_verified,
            "kyc_tier": kyc.tier.value if kyc else "tier_0",
            "trust_score": float(trust.trust_score) if trust else 0.0,
            "risk_level": trust.risk_level if trust else "high",
            "biometric_verified": face_verified or voice_verified,
            "face_verified": face_verified,
            "voice_verified": voice_verified,
            "digital_identity_id": digital_identity.identity_id if digital_identity else None,
            "identity_status": digital_identity.status.value if digital_identity else None,
            "scopes": refresh_token.scopes,
            "aud": client_id,
        }
        
        access_token = create_access_token(subject=user.id, extra_claims=extra_claims)
        
        logger.info(f"Access token refreshed for user {user.id}, client {client_id}")
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes
        }
