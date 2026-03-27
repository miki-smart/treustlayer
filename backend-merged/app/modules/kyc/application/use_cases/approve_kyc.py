"""
ApproveKYCUseCase — approve KYC verification.
"""
import logging
from typing import Optional

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.kyc.domain.entities.kyc_verification import KYCTier, KYCStatus
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository

logger = logging.getLogger(__name__)


class ApproveKYCUseCase:
    """
    Approve KYC verification.
    
    Only KYC approvers and admins can approve.
    Updates KYC tier and triggers trust score recalculation.
    """
    
    def __init__(self, kyc_repo: KYCRepository):
        self.kyc_repo = kyc_repo
    
    async def execute(
        self, verification_id: str, reviewer_id: str, tier: KYCTier, notes: Optional[str] = None
    ):
        """
        Approve KYC verification.
        
        Args:
            verification_id: KYC verification ID
            reviewer_id: Reviewer user ID
            tier: Approved KYC tier
            notes: Optional reviewer notes
        
        Raises:
            NotFoundError: Verification not found
            BadRequestError: Invalid state transition
        """
        kyc = await self.kyc_repo.get_by_id(verification_id)
        if not kyc:
            raise NotFoundError("KYC verification not found")
        
        if kyc.status == KYCStatus.APPROVED:
            raise BadRequestError("KYC already approved")
        
        kyc.approve(reviewer_id, tier)
        
        if notes:
            kyc.notes = notes
        
        await self.kyc_repo.update(kyc)
        
        logger.info(f"KYC {verification_id} approved by {reviewer_id}, tier: {tier.value}")
        
        return kyc
