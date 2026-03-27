"""
UserInfoUseCase — returns OIDC UserInfo claims for a valid access token.
"""
from jose import JWTError

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.modules.auth.application.dto.auth_dto import UserInfoDTO
from app.modules.identity.application.services.identity_service import IdentityService
from app.modules.kyc.application.services.kyc_service import KYCService


class UserInfoUseCase:
    def __init__(
        self,
        identity_service: IdentityService,
        kyc_service: KYCService,
    ) -> None:
        self._identity = identity_service
        self._kyc = kyc_service

    async def execute(self, access_token: str) -> UserInfoDTO:
        try:
            payload = decode_token(access_token)
        except JWTError:
            raise UnauthorizedError("Invalid access token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Token missing subject claim")

        user = await self._identity.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        kyc_status = await self._kyc.get_kyc_status(user_id)
        kyc_tier = kyc_status.tier if kyc_status else "tier_0"
        trust_score = kyc_status.trust_score if kyc_status else 0

        return UserInfoDTO(
            sub=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            email_verified=user.is_email_verified,
            kyc_tier=kyc_tier,
            trust_score=trust_score,
        )
