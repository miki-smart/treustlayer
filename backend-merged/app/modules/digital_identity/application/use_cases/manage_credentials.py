"""
Manage verifiable credentials.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.exceptions import DomainError
from app.modules.digital_identity.domain.entities.digital_identity import IdentityCredential
from app.modules.digital_identity.domain.repositories.identity_repository import DigitalIdentityRepository

logger = logging.getLogger(__name__)


class IssueCredentialUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(
        self,
        identity_id: str,
        credential_type: str,
        credential_data: dict,
        expires_in_days: int = 365,
    ) -> IdentityCredential:
        """
        Issue verifiable credential.
        
        Examples:
        - kyc_verification
        - biometric_verification
        - trust_score
        """
        identity = await self.identity_repo.get_by_id(identity_id)
        if not identity:
            raise DomainError("Digital identity not found")
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        cred = IdentityCredential(
            identity_id=identity_id,
            type=credential_type,
            issuer="trustlayer",
            credential_data=credential_data,
            expires_at=expires_at,
            status="active",
        )
        
        saved = await self.identity_repo.issue_credential(cred)
        logger.info(f"Credential '{credential_type}' issued for identity {identity_id}")
        
        return saved


class ListCredentialsUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(self, identity_id: str) -> List[IdentityCredential]:
        """List all credentials for identity."""
        return await self.identity_repo.get_credentials(identity_id)


class RevokeCredentialUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(self, credential_id: str) -> IdentityCredential:
        """Revoke credential."""
        cred = await self.identity_repo.get_credential(credential_id)
        if not cred:
            raise DomainError("Credential not found")
        
        cred.revoke()
        
        updated = await self.identity_repo.update_credential(cred)
        logger.info(f"Credential {credential_id} revoked")
        
        return updated
