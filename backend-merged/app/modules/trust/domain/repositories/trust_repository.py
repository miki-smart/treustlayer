from abc import ABC, abstractmethod
from typing import Optional

from app.modules.trust.domain.entities.trust_profile import TrustProfile


class TrustRepository(ABC):
    @abstractmethod
    async def create(self, profile: TrustProfile) -> TrustProfile: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[TrustProfile]: ...

    @abstractmethod
    async def update(self, profile: TrustProfile) -> TrustProfile: ...
