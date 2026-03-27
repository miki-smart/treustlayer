"""
TrustProfile — enhanced trust scoring entity.
Pure Python entity.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TrustProfile:
    """
    Enhanced trust profile with biometric and digital identity factors.
    
    Trust Score Components (0-100):
    - Email verified: +20
    - Phone verified: +15
    - KYC tier: +0/+15/+25/+35 (tier 0/1/2/3)
    - Face biometric verified: +10 (NEW)
    - Voice biometric verified: +5 (NEW)
    - Digital identity active: +5 (NEW)
    - Account age: +0 to +10 (over 90 days)
    
    Total: 0-110 (capped at 100)
    """
    
    user_id: str
    trust_score: float = 0.0
    kyc_tier: int = 0
    face_verified: bool = False
    voice_verified: bool = False
    digital_identity_active: bool = False
    factors: dict = field(default_factory=dict)
    last_evaluated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def update_score(
        self,
        email_verified: bool,
        phone_verified: bool,
        kyc_tier: int,
        face_verified: bool,
        voice_verified: bool,
        digital_identity_active: bool,
        account_age_days: int,
    ) -> None:
        """
        Calculate and update trust score.
        """
        score = 0.0
        factors = {}
        
        if email_verified:
            score += 20
            factors["email_verified"] = 20
        
        if phone_verified:
            score += 15
            factors["phone_verified"] = 15
        
        tier_scores = {0: 0, 1: 15, 2: 25, 3: 35}
        tier_score = tier_scores.get(kyc_tier, 0)
        score += tier_score
        factors["kyc_tier"] = tier_score
        
        if face_verified:
            score += 10
            factors["face_biometric"] = 10
        
        if voice_verified:
            score += 5
            factors["voice_biometric"] = 5
        
        if digital_identity_active:
            score += 5
            factors["digital_identity"] = 5
        
        age_score = min(10, (account_age_days / 90) * 10)
        score += age_score
        factors["account_age"] = round(age_score, 2)
        
        self.trust_score = min(100, score)
        self.kyc_tier = kyc_tier
        self.face_verified = face_verified
        self.voice_verified = voice_verified
        self.digital_identity_active = digital_identity_active
        self.factors = factors
        self.last_evaluated = datetime.now(timezone.utc)
