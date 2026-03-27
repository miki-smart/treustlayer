import uuid
from pydantic import BaseModel


class TrustProfileOut(BaseModel):
    userId: str
    trustScore: float
    kycTier: int
    riskLevel: str
    factors: dict
    lastEvaluated: str

    model_config = {"from_attributes": True}


class IntrospectResponse(BaseModel):
    active: bool
    sub: str | None = None
    email: str | None = None
    name: str | None = None
    role: str | None = None
    trust_score: float | None = None
    kyc_tier: int | None = None
    risk_level: str | None = None
    scopes: list[str] = []
    exp: int | None = None
    iss: str | None = None
    client_id: str | None = None
