"""
RefreshTokenUseCase — handles /token with grant_type=refresh_token.
Rotates the refresh token on every use for forward secrecy.
"""
from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token
from app.modules.auth.application.dto.auth_dto import TokenRequestDTO, TokenResponseDTO
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService
from app.modules.identity.application.services.identity_service import IdentityService
from app.modules.kyc.application.services.kyc_service import KYCService
from app.modules.session.application.services.session_service import SessionService


class RefreshTokenUseCase:
    def __init__(
        self,
        identity_service: IdentityService,
        kyc_service: KYCService,
        app_registry_service: AppRegistryService,
        session_service: SessionService,
    ) -> None:
        self._identity = identity_service
        self._kyc = kyc_service
        self._registry = app_registry_service
        self._sessions = session_service

    async def execute(self, dto: TokenRequestDTO) -> TokenResponseDTO:
        # 1 — validate client
        app = await self._registry.validate_client(dto.client_id, dto.client_secret)
        if not app:
            raise UnauthorizedError("Invalid client credentials")

        # 2 — validate refresh token
        token_record = await self._sessions.validate_refresh_token(dto.refresh_token or "")
        if not token_record:
            raise UnauthorizedError("Invalid or expired refresh token")
        if token_record.client_id != dto.client_id:
            raise UnauthorizedError("Refresh token was not issued to this client")

        # 3 — get user
        user = await self._identity.get_user_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User account is inactive")

        # 4 — get fresh KYC data
        kyc_status = await self._kyc.get_kyc_status(user.id)
        kyc_tier = kyc_status.tier if kyc_status else "tier_0"
        trust_score = kyc_status.trust_score if kyc_status else 0

        # 5 — mint new access token
        scopes = token_record.scopes
        extra_claims = {
            "scopes": scopes,
            "aud": dto.client_id,
            "kyc_tier": kyc_tier,
            "trust_score": trust_score,
            "risk_flag": trust_score < 30,
            "username": user.username,
        }
        access_token = create_access_token(
            subject=user.id,
            extra_claims=extra_claims,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # 6 — rotate refresh token
        await self._sessions.revoke_refresh_token(dto.refresh_token or "")
        new_refresh_token = await self._sessions.create_refresh_token(
            user_id=user.id,
            client_id=dto.client_id,
            scopes=scopes,
        )

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            scope=" ".join(scopes),
        )
