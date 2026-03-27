from dataclasses import dataclass, field

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
