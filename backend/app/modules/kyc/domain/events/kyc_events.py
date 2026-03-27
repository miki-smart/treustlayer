from dataclasses import dataclass

from app.core.events import DomainEvent


@dataclass
class KYCSubmittedEvent(DomainEvent):
    user_id: str = ""
    kyc_id: str = ""


@dataclass
class KYCApprovedEvent(DomainEvent):
    user_id: str = ""
    kyc_id: str = ""
    tier: str = ""
    trust_score: int = 0


@dataclass
class KYCRejectedEvent(DomainEvent):
    user_id: str = ""
    kyc_id: str = ""
    reason: str = ""


@dataclass
class RiskUpdatedEvent(DomainEvent):
    user_id: str = ""
    trust_score: int = 0
    risk_flag: bool = False
