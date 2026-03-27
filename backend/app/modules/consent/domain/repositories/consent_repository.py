from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.consent.domain.entities.consent import Consent


class ConsentRepository(ABC):
    @abstractmethod
    async def create(self, consent: Consent) -> Consent: ...

    @abstractmethod
    async def get_active(self, user_id: str, client_id: str) -> Optional[Consent]: ...

    @abstractmethod
    async def get_all_for_user(self, user_id: str) -> List[Consent]: ...

    @abstractmethod
    async def revoke(self, consent_id: str) -> None: ...

    @abstractmethod
    async def update(self, consent: Consent) -> Consent: ...
