from typing import List, Optional

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.entities.user import User, UserRole
from app.modules.identity.domain.repositories.user_repository import UserRepository
from app.modules.identity.infrastructure.persistence.user_model import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            phone_number=user.phone_number,
            role=user.role.value,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username.lower())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_reset_token_hash(self, token_hash: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.password_reset_token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email_verification_token_hash(self, token_hash: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email_verification_token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 50) -> List[User]:
        result = await self._session.execute(
            select(UserModel).order_by(UserModel.created_at.desc()).offset(skip).limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if not model:
            raise ValueError(f"User {user.id} not found")
        model.full_name = user.full_name
        model.phone_number = user.phone_number
        model.role = user.role.value
        model.hashed_password = user.hashed_password
        model.is_active = user.is_active
        model.is_email_verified = user.is_email_verified
        model.updated_at = user.updated_at
        await self._session.flush()
        return self._to_entity(model)

    async def set_email_verification_token(
        self, user_id: str, token_hash: str, expires_at: "datetime"
    ) -> None:
        from sqlalchemy import update as sa_update
        await self._session.execute(
            sa_update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                email_verification_token_hash=token_hash,
                email_verification_expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def clear_email_verification_token(self, user_id: str) -> None:
        from sqlalchemy import update as sa_update
        await self._session.execute(
            sa_update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                email_verification_token_hash=None,
                email_verification_expires_at=None,
            )
        )
        await self._session.flush()

    async def set_password_reset_token(
        self, user_id: str, token_hash: str, expires_at: "datetime"
    ) -> None:
        model = await self._session.get(UserModel, user_id)
        if model:
            model.password_reset_token_hash = token_hash
            model.password_reset_expires_at = expires_at
            await self._session.flush()

    async def clear_password_reset_token(self, user_id: str) -> None:
        model = await self._session.get(UserModel, user_id)
        if model:
            model.password_reset_token_hash = None
            model.password_reset_expires_at = None
            await self._session.flush()

    async def exists_by_email(self, email: str) -> bool:
        result = await self._session.execute(
            select(exists().where(UserModel.email == email.lower()))
        )
        return bool(result.scalar())

    async def exists_by_username(self, username: str) -> bool:
        result = await self._session.execute(
            select(exists().where(UserModel.username == username.lower()))
        )
        return bool(result.scalar())

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=str(model.id),
            email=model.email,
            username=model.username,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            phone_number=model.phone_number,
            role=UserRole(model.role) if model.role else UserRole.USER,
            is_active=model.is_active,
            is_email_verified=model.is_email_verified,
            email_verification_expires_at=model.email_verification_expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
