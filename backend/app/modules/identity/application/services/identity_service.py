"""
IdentityService — public cross-module interface.
Other modules (Auth, KYC, etc.) depend only on this class, not on infrastructure.
"""
from typing import Optional

from app.core.security import verify_password
from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.repositories.user_repository import UserRepository


class IdentityService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Optional[User]:
        """Return User if credentials are valid, None otherwise."""
        user = await self._repo.get_by_username(username_or_email)
        if not user:
            user = await self._repo.get_by_email(username_or_email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return await self._repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self._repo.get_by_email(email)
