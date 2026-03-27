from pydantic import BaseModel, Field


class NationalIDData(BaseModel):
    """Fields extracted from National ID front + back."""
    full_name: str | None = None
    date_of_birth: str | None = None          # YYYY-MM-DD
    id_number: str | None = None
    gender: str | None = None
    nationality: str | None = None
    place_of_birth: str | None = None
    issue_date: str | None = None             # YYYY-MM-DD
    expiry_date: str | None = None            # YYYY-MM-DD
    address: str | None = None
    mrz_line1: str | None = None
    mrz_line2: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class UtilityBillData(BaseModel):
    """Fields extracted from a Utility Bill / Proof of Address."""
    billing_name: str | None = None
    billing_address: str | None = None
    service_provider: str | None = None
    service_type: str | None = None           # electricity/water/gas/internet/etc
    bill_date: str | None = None              # YYYY-MM-DD
    account_number: str | None = None
    amount_due: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class OCRExtractedData(BaseModel):
    """
    Combined, user-editable OCR output returned after document upload.
    The frontend displays these fields for user review before final submission.
    """
    # Identity fields (from National ID)
    full_name: str | None = None
    date_of_birth: str | None = None
    id_number: str | None = None
    gender: str | None = None
    nationality: str | None = None
    place_of_birth: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None

    # Address (resolved from ID or utility bill — utility bill takes priority)
    address: str | None = None

    # Utility bill fields
    billing_name: str | None = None
    service_provider: str | None = None
    service_type: str | None = None
    bill_date: str | None = None
    account_number: str | None = None

    # MRZ (machine-readable zone)
    mrz_line1: str | None = None
    mrz_line2: str | None = None

    # Confidence scores from Gemini
    id_ocr_confidence: float = 0.0
    utility_ocr_confidence: float = 0.0

    # Combined average confidence
    overall_confidence: float = 0.0

    # Which documents were processed
    documents_processed: list[str] = []


class OCRRequest(BaseModel):
    """Metadata sent alongside file uploads (optional overrides)."""
    pass


class OCRResponse(BaseModel):
    """Response from POST /kyc/ocr — returned to frontend for user review."""
    success: bool
    extracted: OCRExtractedData
    warnings: list[str] = []
    model_used: str
