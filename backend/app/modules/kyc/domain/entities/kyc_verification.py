"""
KYCVerification — core KYC entity.
Tiers: tier_0 (unverified), tier_1 (basic), tier_2 (full KYC).
Pure Python: zero framework imports.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class KYCStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class KYCTier(str, Enum):
    TIER_0 = "tier_0"  # unverified
    TIER_1 = "tier_1"  # basic identity verified
    TIER_2 = "tier_2"  # full KYC (ID + face)


@dataclass
class KYCVerification:
    user_id: str
    status: KYCStatus = KYCStatus.PENDING
    tier: KYCTier = KYCTier.TIER_0
    trust_score: int = 0  # 0–100
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    document_url: Optional[str] = None
    face_similarity_score: Optional[float] = None  # 0.0–1.0
    rejection_reason: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None

    def submit(
        self,
        document_type: str,
        document_number: str,
        document_url: str,
        face_similarity_score: Optional[float] = None,
    ) -> None:
        self.document_type = document_type
        self.document_number = document_number
        self.document_url = document_url
        self.face_similarity_score = face_similarity_score
        self.status = KYCStatus.SUBMITTED
        self.updated_at = datetime.now(timezone.utc)

    def approve(self, tier: KYCTier, trust_score: int) -> None:
        self.status = KYCStatus.APPROVED
        self.tier = tier
        self.trust_score = trust_score
        self.verified_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def reject(self, reason: str) -> None:
        self.status = KYCStatus.REJECTED
        self.rejection_reason = reason
        self.updated_at = datetime.now(timezone.utc)
