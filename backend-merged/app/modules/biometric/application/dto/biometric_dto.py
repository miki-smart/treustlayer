"""
Biometric DTOs for API layer.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BiometricCaptureRequest(BaseModel):
    device_info: Optional[dict] = None


class BiometricVerifyRequest(BaseModel):
    device_info: Optional[dict] = None


class BiometricRecordResponse(BaseModel):
    id: str
    user_id: str
    type: str
    status: str
    liveness_score: float
    spoof_probability: float
    quality_score: float
    risk_level: str
    device_info: Optional[dict] = None
    ip_address: Optional[str] = None
    biometric_data_url: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


class BiometricRejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
