"""
KYCVerification — enhanced KYC entity with all frontend fields.
Pure Python entity.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, date
from enum import Enum
from typing import Optional


class KYCStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class KYCTier(str, Enum):
    TIER_0 = "tier_0"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


@dataclass
class KYCVerification:
    """
    Enhanced KYC verification entity.
    
    Includes all fields from frontend registration:
    - Personal info (name, DOB, gender, nationality, place of birth)
    - Document info (type, number, issue/expiry dates)
    - Address (from utility bill)
    - MRZ lines
    - Document URLs
    - OCR confidence scores
    - Risk scores
    """
    
    user_id: str
    status: KYCStatus = KYCStatus.PENDING
    tier: KYCTier = KYCTier.TIER_0
    
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    place_of_birth: Optional[str] = None
    
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    
    address: Optional[str] = None
    billing_name: Optional[str] = None
    service_provider: Optional[str] = None
    service_type: Optional[str] = None
    bill_date: Optional[date] = None
    account_number: Optional[str] = None
    
    mrz_line1: Optional[str] = None
    mrz_line2: Optional[str] = None
    
    id_front_url: Optional[str] = None
    id_back_url: Optional[str] = None
    utility_bill_url: Optional[str] = None
    face_image_url: Optional[str] = None
    
    documents_submitted: list = field(default_factory=list)
    extracted_data: Optional[dict] = None
    
    id_ocr_confidence: float = 0.0
    utility_ocr_confidence: float = 0.0
    overall_confidence: float = 0.0
    
    risk_score: int = 0
    synthetic_id_probability: float = 0.0
    face_similarity_score: Optional[float] = None
    
    reviewer_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def submit(self) -> None:
        """Mark as submitted."""
        self.status = KYCStatus.PENDING
        self.submitted_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def start_review(self) -> None:
        """Start manual review."""
        self.status = KYCStatus.IN_REVIEW
        self.updated_at = datetime.now(timezone.utc)
    
    def approve(self, reviewer_id: str, tier: KYCTier) -> None:
        """Approve KYC."""
        self.status = KYCStatus.APPROVED
        self.tier = tier
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.now(timezone.utc)
        self.verified_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def reject(self, reviewer_id: str, reason: str) -> None:
        """Reject KYC."""
        self.status = KYCStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.rejection_reason = reason
        self.reviewed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def flag(self, reviewer_id: str, reason: str) -> None:
        """Flag as suspicious."""
        self.status = KYCStatus.FLAGGED
        self.reviewer_id = reviewer_id
        self.notes = reason
        self.reviewed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
