"""
RegisterAppUseCase — register new OAuth2 client application.
"""
import logging
from typing import List

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import generate_secure_token, hash_secret
from app.modules.app_registry.domain.entities.app import App
from app.modules.app_registry.domain.repositories.app_repository import AppRepository
from app.modules.identity.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class RegisterAppUseCase:
    """
    Register new OAuth2 client application.
    
    Generates client_id, client_secret, and api_key.
    """
    
    def __init__(self, app_repo: AppRepository, user_repo: UserRepository):
        self.app_repo = app_repo
        self.user_repo = user_repo
    
    async def execute(
        self,
        owner_id: str,
        name: str,
        allowed_scopes: List[str],
        redirect_uris: List[str],
        description: str = "",
        category: str = "general",
        logo_url: str | None = None,
    ) -> tuple[App, str, str]:
        """
        Register new app.
        
        Args:
            owner_id: User ID of app owner
            name: App name
            allowed_scopes: List of scopes app can request
            redirect_uris: List of allowed redirect URIs
            description: App description
            category: App category
            logo_url: App logo URL
        
        Returns:
            Tuple of (App entity, client_secret, api_key)
        
        Raises:
            NotFoundError: Owner not found
            BadRequestError: Invalid input
        """
        # Validate owner exists
        owner = await self.user_repo.get_by_id(owner_id)
        if not owner:
            raise NotFoundError("Owner not found")
        
        # Validate input
        if not name.strip():
            raise BadRequestError("App name is required")
        
        if not allowed_scopes:
            raise BadRequestError("At least one scope is required")
        
        if not redirect_uris:
            raise BadRequestError("At least one redirect URI is required")
        
        # Generate credentials
        client_secret = generate_secure_token(32)
        api_key = generate_secure_token(32)
        
        client_secret_hash = hash_secret(client_secret)
        api_key_hash = hash_secret(api_key)
        
        # Create app
        app = App(
            name=name,
            owner_id=owner_id,
            allowed_scopes=allowed_scopes,
            redirect_uris=redirect_uris,
            description=description,
            category=category,
            logo_url=logo_url,
            client_secret_hash=client_secret_hash,
            api_key_hash=api_key_hash,
        )
        
        saved_app = await self.app_repo.create(app)
        
        logger.info(f"App registered: {saved_app.id} by owner {owner_id}")
        
        return saved_app, client_secret, api_key
