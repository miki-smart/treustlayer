from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.digital_identity.domain.entities.digital_identity import (
    DigitalIdentity,
    IdentityAttribute,
    IdentityCredential,
)


class DigitalIdentityRepository(ABC):
    @abstractmethod
    async def create(self, identity: DigitalIdentity) -> DigitalIdentity: ...

    @abstractmethod
    async def get_by_id(self, identity_id: str) -> Optional[DigitalIdentity]: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[DigitalIdentity]: ...

    @abstractmethod
    async def get_by_unique_id(self, unique_id: str) -> Optional[DigitalIdentity]: ...

    @abstractmethod
    async def update(self, identity: DigitalIdentity) -> DigitalIdentity: ...

    @abstractmethod
    async def add_attribute(self, attr: IdentityAttribute) -> IdentityAttribute: ...

    @abstractmethod
    async def get_attributes(self, identity_id: str) -> List[IdentityAttribute]: ...

    @abstractmethod
    async def get_attribute(self, identity_id: str, key: str) -> Optional[IdentityAttribute]: ...

    @abstractmethod
    async def update_attribute(self, attr: IdentityAttribute) -> IdentityAttribute: ...

    @abstractmethod
    async def delete_attribute(self, identity_id: str, key: str) -> None: ...

    @abstractmethod
    async def issue_credential(self, cred: IdentityCredential) -> IdentityCredential: ...

    @abstractmethod
    async def get_credentials(self, identity_id: str) -> List[IdentityCredential]: ...

    @abstractmethod
    async def get_credential(self, credential_id: str) -> Optional[IdentityCredential]: ...

    @abstractmethod
    async def update_credential(self, cred: IdentityCredential) -> IdentityCredential: ...
