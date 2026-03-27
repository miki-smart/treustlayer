from typing import Optional

from pydantic import BaseModel


class KYCSubmitRequest(BaseModel):
    document_type: str  # "passport" | "national_id" | "driver_license"
    document_number: str
    document_url: str
    face_image_url: Optional[str] = None


class KYCRejectRequest(BaseModel):
    reason: str


class KYCResponse(BaseModel):
    id: str
    user_id: str
    status: str
    tier: str
    trust_score: int
    document_type: Optional[str]
    document_number: Optional[str]
    rejection_reason: Optional[str]
    face_similarity_score: Optional[float]

    model_config = {"from_attributes": True}
