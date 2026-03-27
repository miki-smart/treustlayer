"""
RefreshToken — long-lived token for obtaining new access tokens.
Pure Python entity.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional


@dataclass
class RefreshToken:
    """
    Refresh token entity for OAuth2 token refresh flow.
    
    Attributes:
        user_id: User who owns this token
        client_id: OAuth2 client that issued this token
        token_hash: Hashed token value (stored, not the actual token)
        scopes: List of granted scopes
        expires_at: Token expiration timestamp
        is_revoked: Whether token has been revoked
        device_info: Optional device information (user agent)
        ip_address: Optional IP address where token was issued
    """
    user_id: str
    client_id: str
    token_hash: str
    scopes: List[str]
    expires_at: datetime
    is_revoked: bool = False
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def revoke(self) -> None:
        """Revoke this token."""
        self.is_revoked = True
    
    def update_last_used(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = datetime.now(timezone.utc)
    
    def is_valid(self) -> bool:
        """Check if token is valid (not expired, not revoked)."""
        return not self.is_expired() and not self.is_revoked
