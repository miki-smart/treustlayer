"""
ExchangeTokenUseCase — OIDC token endpoint logic.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_secret,
    verify_pkce,
)
from app.modules.auth.domain.entities.refresh_token import RefreshToken
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


class ExchangeTokenUseCase:
    """
    OIDC Authorization Code Flow - Step 2.
    
    Exchanges authorization code for access_token, refresh_token, and id_token.
    Validates PKCE if present.
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
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: Redirect URI (must match authorization request)
            code_verifier: PKCE code verifier
            device_info: Optional device information
            ip_address: Optional IP address
        
        Returns:
            Dict with access_token, refresh_token, id_token, token_type, expires_in
        
        Raises:
            UnauthorizedError: Invalid code, expired, or PKCE verification failed
            BadRequestError: Missing required parameters
        """
        # 1. Retrieve authorization code
        auth_code = await self.auth_repo.get_authorization_code(code)
        if not auth_code:
            logger.warning(f"Invalid authorization code attempted: {code[:10]}...")
            raise UnauthorizedError("Invalid authorization code")
        
        # 2. Verify code not expired/used
        if auth_code.is_expired():
            logger.warning(f"Expired authorization code used: {code[:10]}...")
            raise UnauthorizedError("Authorization code expired")
        
        if auth_code.is_used:
            logger.warning(f"Already used authorization code: {code[:10]}...")
            raise UnauthorizedError("Authorization code already used")
        
        # 3. Verify client_id and redirect_uri
        if auth_code.client_id != client_id:
            logger.warning(f"Client ID mismatch: expected {auth_code.client_id}, got {client_id}")
            raise UnauthorizedError("Client ID mismatch")
        
        if auth_code.redirect_uri != redirect_uri:
            logger.warning(f"Redirect URI mismatch for client {client_id}")
            raise UnauthorizedError("Redirect URI mismatch")
        
        # 4. Verify PKCE if present
        if auth_code.requires_pkce():
            if not code_verifier:
                raise BadRequestError("code_verifier required for PKCE")
            
            if not verify_pkce(
                code_verifier,
                auth_code.code_challenge,
                auth_code.code_challenge_method or "S256",
            ):
                logger.warning(f"PKCE verification failed for client {client_id}")
                raise UnauthorizedError("PKCE verification failed")
        
        # 5. Mark code as used
        await self.auth_repo.mark_code_as_used(code)
        
        # 6. Load user and related data for enhanced claims
        user = await self.user_repo.get_by_id(auth_code.user_id)
        if not user:
            raise UnauthorizedError("User not found")
        
        # Load KYC data
        kyc = await self.kyc_repo.get_by_user_id(user.id)
        
        # Load trust profile
        trust = await self.trust_repo.get_by_user_id(user.id)
        
        # Check biometric verification
        face_records = await self.biometric_repo.list_by_user_and_type(
            user.id, BiometricType.FACE
        )
        voice_records = await self.biometric_repo.list_by_user_and_type(
            user.id, BiometricType.VOICE
        )
        face_verified = any(r.status == BiometricStatus.VERIFIED for r in face_records)
        voice_verified = any(r.status == BiometricStatus.VERIFIED for r in voice_records)
        
        # Check digital identity
        digital_identity = await self.identity_repo.get_by_user_id(user.id)
        
        # 7. Generate access token with enhanced claims
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
            "scopes": auth_code.scopes,
            "aud": client_id,
        }
        
        access_token = create_access_token(subject=user.id, extra_claims=extra_claims)
        
        # 8. Generate refresh token
        refresh_token_value = generate_secure_token(32)
        refresh_token_hash = hash_secret(refresh_token_value)
        
        refresh_token = RefreshToken(
            user_id=user.id,
            client_id=client_id,
            token_hash=refresh_token_hash,
            scopes=auth_code.scopes,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            device_info=device_info,
            ip_address=ip_address,
        )
        await self.auth_repo.save_refresh_token(refresh_token)
        
        # 9. Generate ID token (OIDC)
        id_token_claims = {
            "aud": client_id,
            "email": user.email,
            "email_verified": user.is_email_verified,
            "name": user.full_name or user.username,
            "preferred_username": user.username,
            "phone_number": user.phone_number,
            "phone_number_verified": user.phone_verified,
        }
        
        id_token = create_access_token(subject=user.id, extra_claims=id_token_claims)
        
        logger.info(
            f"Tokens issued for user {user.id}, client {client_id}, scopes: {auth_code.scopes}"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_value,
            "id_token": id_token,
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes
        }
