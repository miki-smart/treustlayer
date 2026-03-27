"""
Auth domain events.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List


@dataclass
class AuthorizationCodeIssuedEvent:
    """Event emitted when authorization code is issued."""
    user_id: str
    client_id: str
    scopes: List[str]
    timestamp: datetime = datetime.now(timezone.utc)


@dataclass
class TokensIssuedEvent:
    """Event emitted when access/refresh tokens are issued."""
    user_id: str
    client_id: str
    scopes: List[str]
    timestamp: datetime = datetime.now(timezone.utc)


@dataclass
class RefreshTokenRevokedEvent:
    """Event emitted when refresh token is revoked."""
    user_id: str
    token_id: str
    timestamp: datetime = datetime.now(timezone.utc)


@dataclass
class AllTokensRevokedEvent:
    """Event emitted when all user tokens are revoked."""
    user_id: str
    timestamp: datetime = datetime.now(timezone.utc)
