"""
ApproveAppUseCase — approve app for use.
"""
import logging

from app.core.exceptions import NotFoundError
from app.modules.app_registry.domain.repositories.app_repository import AppRepository

logger = logging.getLogger(__name__)


class ApproveAppUseCase:
    """
    Approve app for use.
    
    Only admins can approve apps.
    """
    
    def __init__(self, app_repo: AppRepository):
        self.app_repo = app_repo
    
    async def execute(self, app_id: str) -> None:
        """
        Approve app.
        
        Args:
            app_id: App ID
        
        Raises:
            NotFoundError: App not found
        """
        app = await self.app_repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App not found")
        
        app.approve()
        await self.app_repo.update(app)
        
        logger.info(f"App approved: {app_id}")
