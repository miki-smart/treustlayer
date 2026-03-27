"""
IntrospectUseCase — RFC 7662 token introspection.
Returns active=True with full claims for valid tokens, active=False otherwise.
Used for high-risk validation scenarios (includes trust_score + risk_flag).
"""
from jose import JWTError

from app.core.security import decode_token
from app.modules.auth.application.dto.auth_dto import IntrospectResponseDTO
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService
from app.modules.kyc.application.services.kyc_service import KYCService


class IntrospectUseCase:
    def __init__(
        self,
        app_registry_service: AppRegistryService,
        kyc_service: KYCService,
    ) -> None:
        self._registry = app_registry_service
        self._kyc = kyc_service

    async def execute(
        self, token: str, client_id: str, client_secret: str
    ) -> IntrospectResponseDTO:
        # Validate introspecting client
        app = await self._registry.validate_client(client_id, client_secret)
        if not app:
            return IntrospectResponseDTO(active=False)

        try:
            payload = decode_token(token)
        except JWTError:
            return IntrospectResponseDTO(active=False)

        user_id = payload.get("sub")
        if not user_id:
            return IntrospectResponseDTO(active=False)

        # Always return fresh KYC data so introspection reflects current trust score
        kyc_status = await self._kyc.get_kyc_status(user_id)
        kyc_tier = kyc_status.tier if kyc_status else payload.get("kyc_tier", "tier_0")
        trust_score = kyc_status.trust_score if kyc_status else payload.get("trust_score", 0)

        return IntrospectResponseDTO(
            active=True,
            sub=user_id,
            scopes=" ".join(payload.get("scopes", [])),
            client_id=payload.get("aud"),
            kyc_tier=kyc_tier,
            trust_score=trust_score,
            risk_flag=trust_score < 30,
            exp=payload.get("exp"),
            iss=payload.get("iss"),
        )
