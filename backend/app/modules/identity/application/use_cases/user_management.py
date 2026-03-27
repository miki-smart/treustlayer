from typing import List

from app.core.events import event_bus
from app.core.exceptions import NotFoundError
from app.modules.identity.application.dto.user_dto import UpdateProfileDTO, UserResponseDTO
from app.modules.identity.domain.entities.user import UserRole
from app.modules.identity.domain.events.user_events import UserProfileUpdatedEvent
from app.modules.identity.domain.repositories.user_repository import UserRepository


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, user_id: str) -> UserResponseDTO:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return _to_dto(user)


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, skip: int = 0, limit: int = 50) -> List[UserResponseDTO]:
        users = await self._repo.list_all(skip=skip, limit=limit)
        return [_to_dto(u) for u in users]


class UpdateUserProfileUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, dto: UpdateProfileDTO) -> UserResponseDTO:
        user = await self._repo.get_by_id(dto.user_id)
        if not user:
            raise NotFoundError("User", dto.user_id)

        user.update_profile(full_name=dto.full_name, phone_number=dto.phone_number)
        user = await self._repo.update(user)

        await event_bus.publish(UserProfileUpdatedEvent(user_id=user.id))
        return _to_dto(user)


class AssignRoleUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, user_id: str, new_role: UserRole) -> UserResponseDTO:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        user.change_role(new_role)
        user = await self._repo.update(user)
        return _to_dto(user)


class DeactivateUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, user_id: str) -> UserResponseDTO:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        user.deactivate()
        user = await self._repo.update(user)
        return _to_dto(user)


def _to_dto(user) -> UserResponseDTO:
    from app.modules.identity.application.dto.user_dto import UserResponseDTO
    return UserResponseDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role.value,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        created_at=user.created_at,
    )

