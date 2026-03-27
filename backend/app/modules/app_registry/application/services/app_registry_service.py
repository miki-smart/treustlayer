"""
AppRegistryService — public cross-module interface.
Auth module depends on this to validate clients, redirect URIs, and scopes.
"""
from typing import List, Optional

from app.core.security import verify_secret
from app.modules.app_registry.domain.entities.app import RegisteredApp
from app.modules.app_registry.domain.repositories.app_repository import AppRepository


class AppRegistryService:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def get_app_by_client_id(self, client_id: str) -> Optional[RegisteredApp]:
        return await self._repo.get_by_client_id(client_id)

    async def validate_client(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
    ) -> Optional[RegisteredApp]:
        """
        Returns the app if it is active and approved.
        If client_secret is provided, also verifies the secret.
        """
        app = await self._repo.get_by_client_id(client_id)
        if not app or not app.is_active or not app.is_approved:
            return None
        if client_secret is not None and not verify_secret(client_secret, app.client_secret_hash):
            return None
        return app

    async def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        app = await self._repo.get_by_client_id(client_id)
        return bool(app and app.has_redirect_uri(redirect_uri))

    async def validate_scopes(self, client_id: str, scopes: List[str]) -> bool:
        app = await self._repo.get_by_client_id(client_id)
        return bool(app and app.validate_scopes(scopes))
