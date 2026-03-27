"""
User — core identity entity.
Pure Python dataclass: zero framework imports.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    KYC_APPROVER = "kyc_approver"
    APP_OWNER = "app_owner"


@dataclass
class User:
    email: str
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: UserRole = UserRole.USER
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    is_email_verified: bool = False
    email_verification_expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def verify_email(self) -> None:
        self.is_email_verified = True
        self.updated_at = datetime.now(timezone.utc)

    def update_profile(
        self,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> None:
        if full_name is not None:
            self.full_name = full_name
        if phone_number is not None:
            self.phone_number = phone_number
        self.updated_at = datetime.now(timezone.utc)

    def change_role(self, new_role: UserRole) -> None:
        self.role = new_role
        self.updated_at = datetime.now(timezone.utc)

    def set_password(self, hashed_password: str) -> None:
        self.hashed_password = hashed_password
        self.updated_at = datetime.now(timezone.utc)
