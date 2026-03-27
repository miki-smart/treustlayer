from app.core.events import event_bus
from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.modules.identity.application.dto.user_dto import RegisterUserDTO, UserResponseDTO
from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.events.user_events import UserCreatedEvent
from app.modules.identity.domain.repositories.user_repository import UserRepository


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, dto: RegisterUserDTO) -> UserResponseDTO:
        if await self._repo.exists_by_email(dto.email):
            raise ConflictError(f"Email '{dto.email}' is already registered")
        if await self._repo.exists_by_username(dto.username):
            raise ConflictError(f"Username '{dto.username}' is already taken")

        user = User(
            email=dto.email.lower(),
            username=dto.username.lower(),
            hashed_password=hash_password(dto.password),
            full_name=dto.full_name,
            phone_number=dto.phone_number,
        )
        user = await self._repo.create(user)

        await event_bus.publish(
            UserCreatedEvent(
                user_id=user.id,
                email=user.email,
                username=user.username,
            )
        )

        return _to_response_dto(user)


def _to_response_dto(user: User) -> UserResponseDTO:
    return UserResponseDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role.value,
        full_name=user.full_name,
        phone_number=user.phone_number,
        avatar=user.avatar,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        phone_verified=user.phone_verified,
        created_at=user.created_at,
    )
