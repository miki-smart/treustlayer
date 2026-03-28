"""KYC approver / admin manual verification of email or phone (trust scoring)."""

from app.core.exceptions import NotFoundError
from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.repositories.user_repository import UserRepository


class ManualVerifyEmailUseCase:
    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    async def execute(self, user_id: str) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.verify_email()
        return await self._repo.update(user)


class ManualVerifyPhoneUseCase:
    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    async def execute(self, user_id: str) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        user.verify_phone()
        return await self._repo.update(user)
