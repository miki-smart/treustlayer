from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.modules.identity.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_reset_token_hash(self, token_hash: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_email_verification_token_hash(
        self, token_hash: str
    ) -> Optional[User]: ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 50) -> List[User]: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...

    @abstractmethod
    async def set_password_reset_token(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> None: ...

    @abstractmethod
    async def clear_password_reset_token(self, user_id: str) -> None: ...

    @abstractmethod
    async def set_email_verification_token(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> None: ...

    @abstractmethod
    async def clear_email_verification_token(self, user_id: str) -> None: ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool: ...
