from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.app_registry.domain.entities.app import RegisteredApp


class AppRepository(ABC):
    @abstractmethod
    async def create(self, app: RegisteredApp) -> RegisteredApp: ...

    @abstractmethod
    async def get_by_id(self, app_id: str) -> Optional[RegisteredApp]: ...

    @abstractmethod
    async def get_by_client_id(self, client_id: str) -> Optional[RegisteredApp]: ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 20) -> List[RegisteredApp]: ...

    @abstractmethod
    async def get_by_owner_id(self, owner_id: str, skip: int = 0, limit: int = 50) -> List[RegisteredApp]: ...

    @abstractmethod
    async def update(self, app: RegisteredApp) -> RegisteredApp: ...

    @abstractmethod
    async def exists_by_client_id(self, client_id: str) -> bool: ...
