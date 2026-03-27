from dataclasses import dataclass

from app.core.events import DomainEvent


@dataclass
class ConsentGrantedEvent(DomainEvent):
    user_id: str = ""
    client_id: str = ""
    scopes: str = ""  # space-separated


@dataclass
class ConsentRevokedEvent(DomainEvent):
    user_id: str = ""
    client_id: str = ""
    consent_id: str = ""
