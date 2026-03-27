"""
KYCService — cross-module public interface.
Auth module calls this to embed KYC claims in JWT.
"""
from typing import Optional

from app.modules.kyc.application.dto.kyc_dto import KYCStatusDTO
from app.modules.kyc.domain.entities.kyc_verification import KYCStatus
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository


class KYCService:
    def __init__(self, kyc_repository: KYCRepository) -> None:
        self._repo = kyc_repository

    async def get_kyc_status(self, user_id: str) -> Optional[KYCStatusDTO]:
        kyc = await self._repo.get_by_user_id(user_id)
        if not kyc:
            return None
        return KYCStatusDTO(
            user_id=kyc.user_id,
            tier=kyc.tier.value,
            trust_score=kyc.trust_score,
            is_verified=kyc.status == KYCStatus.APPROVED,
        )
