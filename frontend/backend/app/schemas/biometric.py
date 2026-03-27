import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.biometric import BiometricType, BiometricStatus, RiskLevel


class BiometricRecordOut(BaseModel):
    id: uuid.UUID
    userId: str
    userName: str
    type: BiometricType
    status: BiometricStatus
    livenessScore: float
    spoofProbability: float
    timestamp: str
    riskLevel: RiskLevel

    model_config = {"from_attributes": True}


class BiometricSubmitRequest(BaseModel):
    type: BiometricType = BiometricType.face
    # In a real system this would be a base64-encoded image/audio payload
    payload: str | None = None


class BiometricModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1Score: float
    falseAcceptRate: float
    falseRejectRate: float
    biasMetrics: dict
