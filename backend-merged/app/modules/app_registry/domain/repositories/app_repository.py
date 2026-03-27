"""
AppRepository — repository interface for app registry domain.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.app_registry.domain.entities.app import App


class AppRepository(ABC):
    """Repository interface for OAuth2 client apps."""
    
    @abstractmethod
    async def create(self, app: App) -> App:
        """Create new app."""
        pass
    
    @abstractmethod
    async def get_by_id(self, app_id: str) -> Optional[App]:
        """Get app by ID."""
        pass
    
    @abstractmethod
    async def get_by_client_id(self, client_id: str) -> Optional[App]:
        """Get app by client ID."""
        pass
    
    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> List[App]:
        """List apps owned by user."""
        pass
    
    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 50) -> List[App]:
        """List all apps (admin)."""
        pass
    
    @abstractmethod
    async def list_public(self, skip: int = 0, limit: int = 50) -> List[App]:
        """List public marketplace apps."""
        pass
    
    @abstractmethod
    async def update(self, app: App) -> App:
        """Update app."""
        pass
    
    @abstractmethod
    async def delete(self, app_id: str) -> None:
        """Delete app."""
        pass
