"""
User — core identity entity.

Pure Python dataclass: zero framework imports.
Merged from Backend #1 (structure) + Backend #2 (fields).

Excluded: biometric, cards (out of scope for IDaaS).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """User roles for RBAC."""
    USER = "user"
    ADMIN = "admin"
    KYC_APPROVER = "kyc_approver"
    APP_OWNER = "app_owner"


@dataclass
class User:
    """
    User identity entity.
    
    Fields from Backend #1:
    - email, username, hashed_password
    - role, is_active, is_email_verified
    - email_verification_expires_at
    - created_at, updated_at
    
    Fields from Backend #2:
    - full_name (name in #2)
    - phone_number (phone in #2)
    - phone_verified
    - avatar
    
    Excluded:
    - biometric relationships
    - card relationships
    """
    
    email: str
    username: str
    hashed_password: str
    
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar: Optional[str] = None
    
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_email_verified: bool = False
    phone_verified: bool = False
    
    email_verification_token_hash: Optional[str] = None
    email_verification_expires_at: Optional[datetime] = None
    password_reset_token_hash: Optional[str] = None
    password_reset_expires_at: Optional[datetime] = None
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def verify_email(self) -> None:
        """Mark email as verified."""
        self.is_email_verified = True
        self.email_verification_token_hash = None
        self.email_verification_expires_at = None
        self.updated_at = datetime.now(timezone.utc)
    
    def verify_phone(self) -> None:
        """Mark phone as verified."""
        self.phone_verified = True
        self.updated_at = datetime.now(timezone.utc)
    
    def update_profile(
        self,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> None:
        """Update user profile fields."""
        if full_name is not None:
            self.full_name = full_name
        if phone_number is not None:
            self.phone_number = phone_number
        if avatar is not None:
            self.avatar = avatar
        self.updated_at = datetime.now(timezone.utc)
    
    def change_role(self, new_role: UserRole) -> None:
        """Change user role (admin operation)."""
        self.role = new_role
        self.updated_at = datetime.now(timezone.utc)
    
    def set_password(self, hashed_password: str) -> None:
        """Update password hash."""
        self.hashed_password = hashed_password
        self.password_reset_token_hash = None
        self.password_reset_expires_at = None
        self.updated_at = datetime.now(timezone.utc)
    
    def set_email_verification_token(self, token_hash: str, expires_at: datetime) -> None:
        """Set email verification token."""
        self.email_verification_token_hash = token_hash
        self.email_verification_expires_at = expires_at
        self.updated_at = datetime.now(timezone.utc)
    
    def set_password_reset_token(self, token_hash: str, expires_at: datetime) -> None:
        """Set password reset token."""
        self.password_reset_token_hash = token_hash
        self.password_reset_expires_at = expires_at
        self.updated_at = datetime.now(timezone.utc)
