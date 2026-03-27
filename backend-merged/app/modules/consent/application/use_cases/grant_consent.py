"""
GrantConsentUseCase — grant user consent for data access.
"""
import logging
from typing import List

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.consent.domain.entities.consent_record import ConsentRecord
from app.modules.consent.domain.repositories.consent_repository import ConsentRepository
from app.modules.identity.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class GrantConsentUseCase:
    """
    Grant consent for OAuth2 client.
    
    If consent already exists, updates scopes.
    """
    
    def __init__(
        self, consent_repo: ConsentRepository, user_repo: UserRepository
    ):
        self.consent_repo = consent_repo
        self.user_repo = user_repo
    
    async def execute(
        self, user_id: str, client_id: str, scopes: List[str]
    ) -> ConsentRecord:
        """
        Grant consent.
        
        Args:
            user_id: User ID
            client_id: OAuth2 client ID
            scopes: List of scopes to grant
        
        Returns:
            ConsentRecord entity
        
        Raises:
            NotFoundError: User not found
            BadRequestError: Invalid scopes
        """
        # Validate user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate scopes
        if not scopes:
            raise BadRequestError("At least one scope is required")
        
        # Check if consent already exists
        existing = await self.consent_repo.get_by_user_and_client(user_id, client_id)
        
        if existing:
            # Update existing consent
            existing.update_scopes(scopes)
            existing.is_active = True
            existing.revoked_at = None
            saved = await self.consent_repo.update(existing)
            logger.info(f"Consent updated for user {user_id}, client {client_id}")
        else:
            # Create new consent
            consent = ConsentRecord(
                user_id=user_id, client_id=client_id, scopes=scopes
            )
            saved = await self.consent_repo.create(consent)
            logger.info(f"Consent granted for user {user_id}, client {client_id}")
        
        return saved
