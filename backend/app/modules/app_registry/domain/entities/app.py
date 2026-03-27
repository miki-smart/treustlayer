"""
RegisteredApp — application entity for OAuth2 / OIDC clients.
Pure Python: no framework imports.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class RegisteredApp:
    name: str
    client_id: str
    client_secret_hash: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str = ""
    owner_id: Optional[str] = None
    api_key_hash: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    is_approved: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def approve(self) -> None:
        self.is_approved = True

    def deactivate(self) -> None:
        self.is_active = False

    def update_config(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        allowed_scopes: Optional[List[str]] = None,
        redirect_uris: Optional[List[str]] = None,
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if allowed_scopes is not None:
            self.allowed_scopes = allowed_scopes
        if redirect_uris is not None:
            self.redirect_uris = redirect_uris

    def has_scope(self, scope: str) -> bool:
        return scope in self.allowed_scopes

    def has_redirect_uri(self, redirect_uri: str) -> bool:
        return redirect_uri in self.redirect_uris

    def validate_scopes(self, requested: List[str]) -> bool:
        return all(self.has_scope(s) for s in requested)
