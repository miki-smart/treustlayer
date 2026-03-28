"""Pydantic schemas for trust API responses."""

from pydantic import BaseModel


class TrustProfileResponse(BaseModel):
    user_id: str
    trust_score: float
    risk_level: str
    email_verified: bool
    phone_verified: bool
    kyc_tier: int
    face_verified: bool
    voice_verified: bool
    digital_identity_active: bool
    account_age_days: int
    last_calculated_at: str
