"""
ListAppsUseCase — list apps with various filters.
"""
import logging
from typing import List

from app.modules.app_registry.domain.entities.app import App
from app.modules.app_registry.domain.repositories.app_repository import AppRepository

logger = logging.getLogger(__name__)


class ListAppsUseCase:
    """
    List apps with various filters.
    """
    
    def __init__(self, app_repo: AppRepository):
        self.app_repo = app_repo
    
    async def list_all(self, skip: int = 0, limit: int = 50) -> List[App]:
        """List all apps (admin only)."""
        return await self.app_repo.list_all(skip, limit)
    
    async def list_by_owner(self, owner_id: str) -> List[App]:
        """List apps owned by user."""
        return await self.app_repo.list_by_owner(owner_id)
    
    async def list_marketplace(self, skip: int = 0, limit: int = 50) -> List[App]:
        """List public marketplace apps."""
        return await self.app_repo.list_public(skip, limit)
