"""
ExchangeTokenUseCase — handles /token endpoint for authorization_code grant.

Steps:
  1. Validate client credentials
  2. Retrieve and validate the authorization code
  3. Verify PKCE code_verifier (if code was issued with code_challenge)
  4. Get user profile (identity_service)
  5. Get KYC tier + trust score (kyc_service)
  6. Mint JWT access token with full claims
  7. Create refresh token (session_service)
  8. Return TokenResponseDTO
"""
from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import create_access_token, verify_pkce
from app.modules.auth.application.dto.auth_dto import TokenRequestDTO, TokenResponseDTO
from app.modules.auth.domain.repositories.auth_code_repository import AuthCodeRepository
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService
from app.modules.identity.application.services.identity_service import IdentityService
from app.modules.kyc.application.services.kyc_service import KYCService
from app.modules.session.application.services.session_service import SessionService


class ExchangeTokenUseCase:
    def __init__(
        self,
        code_repository: AuthCodeRepository,
        identity_service: IdentityService,
        kyc_service: KYCService,
        app_registry_service: AppRegistryService,
        session_service: SessionService,
    ) -> None:
        self._codes = code_repository
        self._identity = identity_service
        self._kyc = kyc_service
        self._registry = app_registry_service
        self._sessions = session_service

    async def execute(self, dto: TokenRequestDTO) -> TokenResponseDTO:
        # 1 — validate client credentials
        app = await self._registry.validate_client(dto.client_id, dto.client_secret)
        if not app:
            raise UnauthorizedError("Invalid client credentials")

        # 2 — retrieve auth code
        auth_code = await self._codes.get_by_code(dto.code or "")
        if not auth_code:
            raise ValidationError("Invalid authorization code")
        if auth_code.is_used:
            raise ValidationError("Authorization code has already been used")
        if auth_code.is_expired():
            raise ValidationError("Authorization code has expired")
        if auth_code.client_id != dto.client_id:
            raise ValidationError("Authorization code was not issued to this client")
        if auth_code.redirect_uri != dto.redirect_uri:
            raise ValidationError("redirect_uri mismatch")

        # 3 — verify PKCE
        if auth_code.requires_pkce():
            if not dto.code_verifier:
                raise ValidationError("code_verifier is required for PKCE flow")
            if not verify_pkce(
                dto.code_verifier,
                auth_code.code_challenge,  # type: ignore[arg-type]
                auth_code.code_challenge_method or "S256",
            ):
                raise ValidationError("PKCE code_verifier does not match code_challenge")

        # 4 — get user
        user = await self._identity.get_user_by_id(auth_code.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User account is inactive or not found")

        # 5 — get KYC data
        kyc_status = await self._kyc.get_kyc_status(user.id)
        kyc_tier = kyc_status.tier if kyc_status else "tier_0"
        trust_score = kyc_status.trust_score if kyc_status else 0
        risk_flag = trust_score < 30

        # 6 — mint JWT
        scopes = auth_code.scopes
        extra_claims = {
            "scopes": scopes,
            "aud": dto.client_id,
            "kyc_tier": kyc_tier,
            "trust_score": trust_score,
            "risk_flag": risk_flag,
            "username": user.username,
        }
        if "profile.email" in scopes:
            extra_claims["email"] = user.email
        if "profile.basic" in scopes:
            extra_claims["full_name"] = user.full_name

        access_token = create_access_token(
            subject=user.id,
            extra_claims=extra_claims,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # 7 — consume code and create refresh token
        await self._codes.consume(auth_code.code)

        refresh_token = None
        if "offline_access" in scopes:
            refresh_token = await self._sessions.create_refresh_token(
                user_id=user.id,
                client_id=dto.client_id,
                scopes=scopes,
            )

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            scope=" ".join(scopes),
        )
