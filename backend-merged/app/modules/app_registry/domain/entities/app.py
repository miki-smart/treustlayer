"""
App — OAuth2 client application.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class App:
    """
    OAuth2 client application.
    
    Attributes:
        name: Application name
        owner_id: User who owns this app
        allowed_scopes: List of scopes this app can request
        redirect_uris: List of allowed redirect URIs
        client_id: OAuth2 client ID
        client_secret_hash: Hashed client secret
        api_key_hash: Hashed API key (for direct API access)
        description: App description
        logo_url: App logo URL
        category: App category (identity, finance, health, etc.)
        is_active: Whether app is active
        is_approved: Whether app is approved by admin
        is_public: Whether app is visible in marketplace
    """
    name: str
    owner_id: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    client_id: str = field(default_factory=lambda: f"app_{uuid.uuid4().hex[:16]}")
    client_secret_hash: str = ""
    api_key_hash: str = ""
    description: str = ""
    logo_url: Optional[str] = None
    category: str = "general"
    is_active: bool = True
    is_approved: bool = False
    is_public: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def approve(self) -> None:
        """Approve app for use and list it in the public marketplace."""
        self.is_approved = True
        self.is_public = True
        self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate app."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def make_public(self) -> None:
        """Make app visible in marketplace."""
        self.is_public = True
        self.updated_at = datetime.now(timezone.utc)
    
    def update_credentials(self, client_secret_hash: str, api_key_hash: str) -> None:
        """Update app credentials."""
        self.client_secret_hash = client_secret_hash
        self.api_key_hash = api_key_hash
        self.updated_at = datetime.now(timezone.utc)
