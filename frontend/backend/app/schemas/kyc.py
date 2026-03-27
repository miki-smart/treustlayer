import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.models.kyc import KYCStatus
from app.schemas.ocr import OCRExtractedData


class KYCApplicationOut(BaseModel):
    id: uuid.UUID
    userId: str
    applicantName: str
    email: str
    status: KYCStatus
    riskScore: int
    documentsSubmitted: list[str]
    ocrConfidence: float
    syntheticIdProbability: float
    submittedAt: str
    reviewedAt: str | None = None
    reviewer: str | None = None
    notes: str | None = None
    extractedData: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class KYCSubmitRequest(BaseModel):
    documents_submitted: list[str]
    # User-confirmed OCR data (edited after reviewing the OCR results).
    # If provided, real OCR confidence values are used instead of simulated ones.
    extracted_data: OCRExtractedData | None = None


class KYCReviewRequest(BaseModel):
    status: KYCStatus
    notes: str | None = None
