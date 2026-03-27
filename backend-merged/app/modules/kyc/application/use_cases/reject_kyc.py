"""
RejectKYCUseCase — reject KYC verification.
"""
import logging

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.kyc.domain.entities.kyc_verification import KYCStatus
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository

logger = logging.getLogger(__name__)


class RejectKYCUseCase:
    """
    Reject KYC verification.
    
    Only KYC approvers and admins can reject.
    """
    
    def __init__(self, kyc_repo: KYCRepository):
        self.kyc_repo = kyc_repo
    
    async def execute(self, verification_id: str, reviewer_id: str, reason: str):
        """
        Reject KYC verification.
        
        Args:
            verification_id: KYC verification ID
            reviewer_id: Reviewer user ID
            reason: Rejection reason
        
        Raises:
            NotFoundError: Verification not found
            BadRequestError: Invalid state transition
        """
        kyc = await self.kyc_repo.get_by_id(verification_id)
        if not kyc:
            raise NotFoundError("KYC verification not found")
        
        if kyc.status == KYCStatus.APPROVED:
            raise BadRequestError("Cannot reject approved KYC")
        
        kyc.reject(reviewer_id, reason)
        
        await self.kyc_repo.update(kyc)
        
        logger.info(f"KYC {verification_id} rejected by {reviewer_id}, reason: {reason}")
        
        return kyc
