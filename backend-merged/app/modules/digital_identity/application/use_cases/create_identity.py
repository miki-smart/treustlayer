"""
CreateDigitalIdentityUseCase — create digital identity for user.
"""
import hashlib
import logging

from app.core.exceptions import DomainError
from app.modules.digital_identity.domain.entities.digital_identity import DigitalIdentity, IdentityStatus
from app.modules.digital_identity.domain.repositories.identity_repository import DigitalIdentityRepository

logger = logging.getLogger(__name__)


class CreateDigitalIdentityUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(self, user_id: str) -> DigitalIdentity:
        """
        Create digital identity for user.
        
        Steps:
        1. Check if identity already exists
        2. Generate unique DID
        3. Create identity
        """
        existing = await self.identity_repo.get_by_user_id(user_id)
        if existing:
            raise DomainError("Digital identity already exists for this user")
        
        unique_id = self._generate_did(user_id)
        
        identity = DigitalIdentity(
            user_id=user_id,
            unique_id=unique_id,
            status=IdentityStatus.PENDING,
        )
        
        saved = await self.identity_repo.create(identity)
        
        logger.info(f"Digital identity created: {saved.unique_id} for user {user_id}")
        
        return saved
    
    def _generate_did(self, user_id: str) -> str:
        """
        Generate DID identifier.
        
        Format: did:trustlayer:<hash>
        """
        hash_input = f"trustlayer:{user_id}"
        hash_hex = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return f"did:trustlayer:{hash_hex}"
