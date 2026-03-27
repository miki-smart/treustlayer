"""
BiometricRecord — face or voice verification record.
Pure Python entity.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class BiometricType(str, Enum):
    FACE = "face"
    VOICE = "voice"


class BiometricStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    FLAGGED = "flagged"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class BiometricRecord:
    """
    Biometric verification record.
    
    Tracks face or voice biometric verification attempts.
    """
    
    user_id: str
    type: BiometricType
    status: BiometricStatus = BiometricStatus.PENDING
    
    liveness_score: float = 0.0
    spoof_probability: float = 0.0
    quality_score: float = 0.0
    
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    device_info: Optional[dict] = None
    ip_address: Optional[str] = None
    
    biometric_data_url: Optional[str] = None
    biometric_hash: Optional[str] = None
    
    verified_at: Optional[datetime] = None
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def verify(self) -> None:
        """Mark biometric as verified."""
        self.status = BiometricStatus.VERIFIED
        self.verified_at = datetime.now(timezone.utc)
    
    def fail(self) -> None:
        """Mark biometric as failed."""
        self.status = BiometricStatus.FAILED
    
    def flag(self) -> None:
        """Flag biometric as suspicious."""
        self.status = BiometricStatus.FLAGGED
    
    def calculate_risk_level(self) -> RiskLevel:
        """Calculate risk level based on scores."""
        if self.spoof_probability > 0.7 or self.liveness_score < 0.3:
            return RiskLevel.HIGH
        elif self.spoof_probability > 0.4 or self.liveness_score < 0.6:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
