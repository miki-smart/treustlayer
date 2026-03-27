"""
AuthorizeUseCase — OIDC authorization endpoint logic.
"""
import logging
from typing import List, Optional

from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import verify_password
from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.repositories.auth_repository import AuthRepository
from app.modules.identity.domain.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthorizeUseCase:
    """
    OIDC Authorization Code Flow - Step 1.
    
    Validates user credentials, client_id, redirect_uri, and scopes.
    Issues authorization code for token exchange.
    """
    
    def __init__(
        self,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
    ):
        self.auth_repo = auth_repo
        self.user_repo = user_repo
    
    async def execute(
        self,
        email: str,
        password: str,
        client_id: str,
        redirect_uri: str,
        scopes: List[str],
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
    ) -> AuthorizationCode:
        """
        Execute authorization flow.
        
        Args:
            email: User email
            password: User password
            client_id: OAuth2 client ID
            redirect_uri: Redirect URI after authorization
            scopes: Requested scopes
            state: Optional state parameter
            code_challenge: Optional PKCE code challenge
            code_challenge_method: PKCE method (S256 or plain)
        
        Returns:
            AuthorizationCode entity
        
        Raises:
            UnauthorizedError: Invalid credentials or inactive user
            BadRequestError: Invalid client_id, redirect_uri, or scopes
        """
        # 1. Validate user credentials
        user = await self.user_repo.get_by_email(email.lower())
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise UnauthorizedError("Invalid credentials")
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {user.id}")
            raise UnauthorizedError("Invalid credentials")
        
        if not user.is_active:
            logger.warning(f"Login attempt for deactivated user: {user.id}")
            raise UnauthorizedError("Account is deactivated")
        
        # 2. Validate client_id (simplified - in full implementation, check app_registry)
        # For now, accept any client_id (will be validated in Feature #5)
        if not client_id:
            raise BadRequestError("client_id is required")
        
        # 3. Validate redirect_uri (simplified - in full implementation, check against whitelist)
        if not redirect_uri:
            raise BadRequestError("redirect_uri is required")
        
        # 4. Validate scopes (simplified - accept common OIDC scopes)
        valid_scopes = {"openid", "profile", "email", "phone", "kyc_status", "trust_score", "biometric", "identity"}
        invalid_scopes = set(scopes) - valid_scopes
        if invalid_scopes:
            raise BadRequestError(f"Invalid scopes: {invalid_scopes}")
        
        if "openid" not in scopes:
            raise BadRequestError("'openid' scope is required for OIDC")
        
        # 5. Generate authorization code
        code = AuthorizationCode(
            client_id=client_id,
            user_id=user.id,
            redirect_uri=redirect_uri,
            scopes=scopes,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        
        # 6. Store code
        saved_code = await self.auth_repo.save_authorization_code(code)
        
        logger.info(
            f"Authorization code issued for user {user.id}, client {client_id}, scopes: {scopes}"
        )
        
        return saved_code
