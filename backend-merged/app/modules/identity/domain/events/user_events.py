from dataclasses import dataclass

from app.core.events import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    user_id: str = ""
    email: str = ""
    username: str = ""


@dataclass
class UserProfileUpdatedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class UserDeactivatedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class EmailVerifiedEvent(DomainEvent):
    user_id: str = ""
    email: str = ""


@dataclass
class PhoneVerifiedEvent(DomainEvent):
    user_id: str = ""
    phone_number: str = ""
