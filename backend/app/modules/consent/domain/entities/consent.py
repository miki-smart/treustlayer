"""
Consent — records that a user has granted specific scopes to a specific client.
Pure Python entity.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Consent:
    user_id: str
    client_id: str
    scopes: List[str]
    is_active: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None

    def revoke(self) -> None:
        self.is_active = False
        self.revoked_at = datetime.now(timezone.utc)

    def covers_scopes(self, requested: List[str]) -> bool:
        """Return True if all requested scopes are covered by this consent."""
        return all(s in self.scopes for s in requested)
