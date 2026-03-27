"""
DigitalIdentity — verifiable digital identity entity.
Pure Python entity.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class IdentityStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class DigitalIdentity:
    """
    Digital Identity (DID-like system).
    
    Represents a user's verifiable digital identity.
    """
    
    user_id: str
    unique_id: str
    status: IdentityStatus = IdentityStatus.PENDING
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def activate(self) -> None:
        """Activate digital identity."""
        self.status = IdentityStatus.ACTIVE
        self.last_verified = datetime.now(timezone.utc)
    
    def suspend(self) -> None:
        """Suspend digital identity."""
        self.status = IdentityStatus.SUSPENDED
    
    def revoke(self) -> None:
        """Revoke digital identity."""
        self.status = IdentityStatus.REVOKED
    
    def verify(self) -> None:
        """Update last verified timestamp."""
        self.last_verified = datetime.now(timezone.utc)


@dataclass
class IdentityAttribute:
    """
    Identity attribute (key-value pair).
    
    Examples: name, email, phone, address, etc.
    """
    
    identity_id: str
    key: str
    value: str
    is_shared: bool = False
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IdentityCredential:
    """
    Verifiable credential issued by TrustLayer.
    
    Examples:
    - KYC verification credential
    - Biometric verification credential
    - Trust score credential
    """
    
    identity_id: str
    type: str
    issuer: str
    credential_data: dict
    expires_at: datetime
    status: str = "active"
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def revoke(self) -> None:
        """Revoke credential."""
        self.status = "revoked"
    
    def is_expired(self) -> bool:
        """Check if credential is expired."""
        return datetime.now(timezone.utc) > self.expires_at
