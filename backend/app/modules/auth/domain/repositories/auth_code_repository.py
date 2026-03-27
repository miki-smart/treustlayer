from abc import ABC, abstractmethod
from typing import Optional

from app.modules.auth.domain.entities.authorization_code import AuthorizationCode


class AuthCodeRepository(ABC):
    @abstractmethod
    async def create(self, code: AuthorizationCode) -> AuthorizationCode: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[AuthorizationCode]: ...

    @abstractmethod
    async def consume(self, code: str) -> None: ...
