"""
RevokeConsentUseCase — revoke user consent.
"""
import logging

from app.core.exceptions import NotFoundError
from app.modules.consent.domain.repositories.consent_repository import ConsentRepository

logger = logging.getLogger(__name__)


class RevokeConsentUseCase:
    """
    Revoke consent for OAuth2 client.
    """
    
    def __init__(self, consent_repo: ConsentRepository):
        self.consent_repo = consent_repo
    
    async def execute(self, user_id: str, client_id: str) -> None:
        """
        Revoke consent.
        
        Args:
            user_id: User ID
            client_id: OAuth2 client ID
        
        Raises:
            NotFoundError: Consent not found
        """
        consent = await self.consent_repo.get_by_user_and_client(user_id, client_id)
        
        if not consent:
            raise NotFoundError("Consent not found")
        
        consent.revoke()
        await self.consent_repo.update(consent)
        
        logger.info(f"Consent revoked for user {user_id}, client {client_id}")
