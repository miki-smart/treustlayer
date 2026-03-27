"""
SQLAlchemy implementation of AppRepository.
"""
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.app_registry.domain.entities.app import App
from app.modules.app_registry.domain.repositories.app_repository import AppRepository
from app.modules.app_registry.infrastructure.persistence.app_model import AppModel


class SQLAlchemyAppRepository(AppRepository):
    """SQLAlchemy implementation of app repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, app: App) -> App:
        """Create new app."""
        model = AppModel(
            id=app.id,
            name=app.name,
            owner_id=app.owner_id,
            client_id=app.client_id,
            client_secret_hash=app.client_secret_hash,
            api_key_hash=app.api_key_hash,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            logo_url=app.logo_url,
            category=app.category,
            is_active=app.is_active,
            is_approved=app.is_approved,
            is_public=app.is_public,
        )
        self.session.add(model)
        await self.session.flush()
        return app
    
    async def get_by_id(self, app_id: str) -> Optional[App]:
        """Get app by ID."""
        result = await self.session.execute(
            select(AppModel).where(AppModel.id == app_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_entity(model)
    
    async def get_by_client_id(self, client_id: str) -> Optional[App]:
        """Get app by client ID."""
        result = await self.session.execute(
            select(AppModel).where(AppModel.client_id == client_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._model_to_entity(model)
    
    async def list_by_owner(self, owner_id: str) -> List[App]:
        """List apps owned by user."""
        result = await self.session.execute(
            select(AppModel)
            .where(AppModel.owner_id == owner_id)
            .order_by(AppModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def list_all(self, skip: int = 0, limit: int = 50) -> List[App]:
        """List all apps (admin)."""
        result = await self.session.execute(
            select(AppModel).order_by(AppModel.created_at.desc()).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def list_public(self, skip: int = 0, limit: int = 50) -> List[App]:
        """List public marketplace apps."""
        result = await self.session.execute(
            select(AppModel)
            .where(AppModel.is_public == True, AppModel.is_approved == True)
            .order_by(AppModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def update(self, app: App) -> App:
        """Update app."""
        result = await self.session.execute(
            select(AppModel).where(AppModel.id == app.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.name = app.name
            model.allowed_scopes = app.allowed_scopes
            model.redirect_uris = app.redirect_uris
            model.description = app.description
            model.logo_url = app.logo_url
            model.category = app.category
            model.is_active = app.is_active
            model.is_approved = app.is_approved
            model.is_public = app.is_public
            model.client_secret_hash = app.client_secret_hash
            model.api_key_hash = app.api_key_hash
            model.updated_at = app.updated_at
            await self.session.flush()
        return app
    
    async def delete(self, app_id: str) -> None:
        """Delete app."""
        await self.session.execute(delete(AppModel).where(AppModel.id == app_id))
        await self.session.flush()
    
    def _model_to_entity(self, model: AppModel) -> App:
        """Convert model to entity."""
        return App(
            id=str(model.id),
            name=model.name,
            owner_id=str(model.owner_id),
            client_id=model.client_id,
            client_secret_hash=model.client_secret_hash,
            api_key_hash=model.api_key_hash,
            allowed_scopes=model.allowed_scopes,
            redirect_uris=model.redirect_uris,
            description=model.description,
            logo_url=model.logo_url,
            category=model.category,
            is_active=model.is_active,
            is_approved=model.is_approved,
            is_public=model.is_public,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
