"""
RefreshToken entity — stored and managed by the Session module.
Pure Python.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.config import settings


@dataclass
class RefreshToken:
    user_id: str
    client_id: str
    scopes: List[str]
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def revoke(self) -> None:
        self.is_revoked = True

    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired()
