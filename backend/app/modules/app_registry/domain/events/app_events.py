from dataclasses import dataclass

from app.core.events import DomainEvent


@dataclass
class AppRegisteredEvent(DomainEvent):
    app_id: str = ""
    client_id: str = ""
    name: str = ""


@dataclass
class AppApprovedEvent(DomainEvent):
    app_id: str = ""
    client_id: str = ""
