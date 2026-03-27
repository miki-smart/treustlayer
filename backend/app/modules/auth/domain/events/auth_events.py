from dataclasses import dataclass

from app.core.events import DomainEvent


@dataclass
class TokenIssuedEvent(DomainEvent):
    user_id: str = ""
    client_id: str = ""
    scopes: str = ""  # space-separated


@dataclass
class TokenRevokedEvent(DomainEvent):
    user_id: str = ""
    client_id: str = ""
