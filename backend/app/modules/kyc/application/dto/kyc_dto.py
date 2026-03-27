from dataclasses import dataclass
from typing import Optional


@dataclass
class SubmitKYCDTO:
    user_id: str
    document_type: str
    document_number: str
    document_url: str
    # AI integration: mock face similarity (0.0–1.0)
    face_image_url: Optional[str] = None


@dataclass
class KYCResponseDTO:
    id: str
    user_id: str
    status: str
    tier: str
    trust_score: int
    document_type: Optional[str]
    document_number: Optional[str]
    rejection_reason: Optional[str]
    face_similarity_score: Optional[float]


@dataclass
class KYCStatusDTO:
    """Lightweight status — exposed to other modules via KYCService."""
    user_id: str
    tier: str
    trust_score: int
    is_verified: bool
