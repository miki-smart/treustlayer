from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RegisterUserDTO:
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


@dataclass
class UserResponseDTO:
    id: str
    email: str
    username: str
    role: str
    full_name: Optional[str]
    phone_number: Optional[str]
    is_active: bool
    is_email_verified: bool
    created_at: datetime


@dataclass
class UpdateProfileDTO:
    user_id: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
