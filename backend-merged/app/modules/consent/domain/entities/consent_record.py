"""
ConsentRecord — user consent for data access.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class ConsentRecord:
    """
    User consent for OAuth2 client data access.
    
    Attributes:
        user_id: User who granted consent
        client_id: OAuth2 client that received consent
        scopes: List of granted scopes
        is_active: Whether consent is currently active
    """
    user_id: str
    client_id: str
    scopes: List[str]
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: datetime | None = None
    
    def revoke(self) -> None:
        """Revoke this consent."""
        self.is_active = False
        self.revoked_at = datetime.now(timezone.utc)
    
    def update_scopes(self, new_scopes: List[str]) -> None:
        """Update granted scopes."""
        self.scopes = new_scopes
