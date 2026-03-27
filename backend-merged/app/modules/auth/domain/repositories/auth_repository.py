"""
AuthRepository — repository interface for auth domain.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.entities.refresh_token import RefreshToken


class AuthRepository(ABC):
    """Repository interface for authentication entities."""
    
    @abstractmethod
    async def save_authorization_code(self, code: AuthorizationCode) -> AuthorizationCode:
        """Save authorization code to storage."""
        pass
    
    @abstractmethod
    async def get_authorization_code(self, code: str) -> Optional[AuthorizationCode]:
        """Retrieve authorization code by code value."""
        pass
    
    @abstractmethod
    async def mark_code_as_used(self, code: str) -> None:
        """Mark authorization code as used (prevents replay attacks)."""
        pass
    
    @abstractmethod
    async def save_refresh_token(self, token: RefreshToken) -> RefreshToken:
        """Save refresh token to storage."""
        pass
    
    @abstractmethod
    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve refresh token by hash."""
        pass
    
    @abstractmethod
    async def revoke_refresh_token(self, token_id: str) -> None:
        """Revoke a specific refresh token."""
        pass
    
    @abstractmethod
    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user (sign out all devices)."""
        pass
    
    @abstractmethod
    async def list_user_tokens(self, user_id: str) -> List[RefreshToken]:
        """List all active refresh tokens for a user."""
        pass
    
    @abstractmethod
    async def delete_expired_codes(self) -> int:
        """Delete expired authorization codes (cleanup task)."""
        pass
    
    @abstractmethod
    async def delete_expired_tokens(self) -> int:
        """Delete expired refresh tokens (cleanup task)."""
        pass
