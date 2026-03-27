"""
Manage identity attributes.
"""
import logging
from typing import List

from app.core.exceptions import DomainError
from app.modules.digital_identity.domain.entities.digital_identity import IdentityAttribute
from app.modules.digital_identity.domain.repositories.identity_repository import DigitalIdentityRepository

logger = logging.getLogger(__name__)


class AddAttributeUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(
        self,
        identity_id: str,
        key: str,
        value: str,
        is_shared: bool = False,
    ) -> IdentityAttribute:
        """Add attribute to identity."""
        identity = await self.identity_repo.get_by_id(identity_id)
        if not identity:
            raise DomainError("Digital identity not found")
        
        existing = await self.identity_repo.get_attribute(identity_id, key)
        if existing:
            raise DomainError(f"Attribute '{key}' already exists")
        
        attr = IdentityAttribute(
            identity_id=identity_id,
            key=key,
            value=value,
            is_shared=is_shared,
        )
        
        saved = await self.identity_repo.add_attribute(attr)
        logger.info(f"Attribute '{key}' added to identity {identity_id}")
        
        return saved


class ListAttributesUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(self, identity_id: str) -> List[IdentityAttribute]:
        """List all attributes for identity."""
        return await self.identity_repo.get_attributes(identity_id)


class UpdateAttributeUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(
        self,
        identity_id: str,
        key: str,
        value: str | None = None,
        is_shared: bool | None = None,
    ) -> IdentityAttribute:
        """Update attribute."""
        attr = await self.identity_repo.get_attribute(identity_id, key)
        if not attr:
            raise DomainError(f"Attribute '{key}' not found")
        
        if value is not None:
            attr.value = value
        if is_shared is not None:
            attr.is_shared = is_shared
        
        updated = await self.identity_repo.update_attribute(attr)
        logger.info(f"Attribute '{key}' updated for identity {identity_id}")
        
        return updated


class DeleteAttributeUseCase:
    def __init__(self, identity_repo: DigitalIdentityRepository):
        self.identity_repo = identity_repo

    async def execute(self, identity_id: str, key: str) -> None:
        """Delete attribute."""
        await self.identity_repo.delete_attribute(identity_id, key)
        logger.info(f"Attribute '{key}' deleted from identity {identity_id}")
