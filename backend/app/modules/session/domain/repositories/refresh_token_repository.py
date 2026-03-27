from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.session.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]: ...

    @abstractmethod
    async def revoke_by_hash(self, token_hash: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user_client(
        self, user_id: str, client_id: str
    ) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None: ...

    @abstractmethod
    async def revoke_by_id(self, token_id: str) -> None: ...

    @abstractmethod
    async def list_active_for_user(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> List[RefreshToken]: ...
