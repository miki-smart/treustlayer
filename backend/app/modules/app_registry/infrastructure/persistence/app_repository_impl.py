from typing import List, Optional

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.app_registry.domain.entities.app import RegisteredApp
from app.modules.app_registry.domain.repositories.app_repository import AppRepository
from app.modules.app_registry.infrastructure.persistence.app_model import RegisteredAppModel


class SQLAlchemyAppRepository(AppRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, app: RegisteredApp) -> RegisteredApp:
        model = RegisteredAppModel(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            client_secret_hash=app.client_secret_hash,
            api_key_hash=app.api_key_hash,
            owner_id=app.owner_id,
            description=app.description,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            is_active=app.is_active,
            is_approved=app.is_approved,
            created_at=app.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, app_id: str) -> Optional[RegisteredApp]:
        result = await self._session.execute(
            select(RegisteredAppModel).where(RegisteredAppModel.id == app_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_client_id(self, client_id: str) -> Optional[RegisteredApp]:
        result = await self._session.execute(
            select(RegisteredAppModel).where(
                RegisteredAppModel.client_id == client_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[RegisteredApp]:
        result = await self._session.execute(
            select(RegisteredAppModel).offset(skip).limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, app: RegisteredApp) -> RegisteredApp:
        model = await self._session.get(RegisteredAppModel, app.id)
        if not model:
            raise ValueError(f"App {app.id} not found")
        model.name = app.name
        model.description = app.description
        model.allowed_scopes = app.allowed_scopes
        model.redirect_uris = app.redirect_uris
        model.is_active = app.is_active
        model.is_approved = app.is_approved
        model.client_secret_hash = app.client_secret_hash
        model.api_key_hash = app.api_key_hash
        model.owner_id = app.owner_id
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_owner_id(
        self, owner_id: str, skip: int = 0, limit: int = 50
    ) -> list[RegisteredApp]:
        result = await self._session.execute(
            select(RegisteredAppModel)
            .where(RegisteredAppModel.owner_id == owner_id)
            .order_by(RegisteredAppModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def exists_by_client_id(self, client_id: str) -> bool:
        result = await self._session.execute(
            select(exists().where(RegisteredAppModel.client_id == client_id))
        )
        return bool(result.scalar())

    async def get_by_api_key_hash(self, api_key_hash: str) -> Optional[RegisteredApp]:
        result = await self._session.execute(
            select(RegisteredAppModel).where(
                RegisteredAppModel.api_key_hash == api_key_hash,
                RegisteredAppModel.is_active.is_(True),
                RegisteredAppModel.is_approved.is_(True),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: RegisteredAppModel) -> RegisteredApp:
        return RegisteredApp(
            id=str(model.id),
            name=model.name,
            client_id=model.client_id,
            client_secret_hash=model.client_secret_hash,
            api_key_hash=model.api_key_hash,
            owner_id=model.owner_id,
            description=model.description or "",
            allowed_scopes=list(model.allowed_scopes or []),
            redirect_uris=list(model.redirect_uris or []),
            is_active=model.is_active,
            is_approved=model.is_approved,
            created_at=model.created_at,
        )
