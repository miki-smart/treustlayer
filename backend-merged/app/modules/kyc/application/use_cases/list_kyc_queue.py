"""
ListKYCQueueUseCase — list pending KYC submissions.
"""
import logging
from typing import List

from app.modules.kyc.domain.entities.kyc_verification import KYCStatus, KYCVerification
from app.modules.kyc.domain.repositories.kyc_repository import KYCRepository

logger = logging.getLogger(__name__)


class ListKYCQueueUseCase:
    """
    List KYC submissions in review queue.
    
    Only KYC approvers and admins can access.
    """
    
    def __init__(self, kyc_repo: KYCRepository):
        self.kyc_repo = kyc_repo
    
    async def execute(
        self, status: KYCStatus = KYCStatus.PENDING, skip: int = 0, limit: int = 50
    ) -> List[KYCVerification]:
        """
        List KYC submissions by status.
        
        Args:
            status: Filter by status (default: PENDING)
            skip: Pagination offset
            limit: Pagination limit
        
        Returns:
            List of KYC verifications
        """
        verifications = await self.kyc_repo.list_by_status(status, skip, limit)
        
        logger.info(f"Listed {len(verifications)} KYC submissions with status {status.value}")
        
        return verifications
