"""
ListUserConsentsUseCase — list all consents for a user.
"""
import logging
from typing import List

from app.modules.consent.domain.entities.consent_record import ConsentRecord
from app.modules.consent.domain.repositories.consent_repository import ConsentRepository

logger = logging.getLogger(__name__)


class ListUserConsentsUseCase:
    """
    List all consents for a user.
    """
    
    def __init__(self, consent_repo: ConsentRepository):
        self.consent_repo = consent_repo
    
    async def execute(self, user_id: str) -> List[ConsentRecord]:
        """
        List user consents.
        
        Args:
            user_id: User ID
        
        Returns:
            List of consent records
        """
        consents = await self.consent_repo.list_by_user(user_id)
        
        logger.info(f"Listed {len(consents)} consents for user {user_id}")
        
        return consents
