"""
AuthorizationCode — single-use, short-lived PKCE-capable auth code.
Pure Python entity.
"""
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional


@dataclass
class AuthorizationCode:
    client_id: str
    user_id: str
    redirect_uri: str
    scopes: List[str]
    code: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    is_used: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def consume(self) -> None:
        self.is_used = True

    def requires_pkce(self) -> bool:
        return self.code_challenge is not None
