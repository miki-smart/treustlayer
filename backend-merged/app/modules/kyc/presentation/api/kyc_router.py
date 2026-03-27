"""
KYC router — document submission and approval.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from typing import List

from app.api.dependencies import DBSession, CurrentUserId, require_admin

router = APIRouter()


class KYCResponse(BaseModel):
    id: str
    user_id: str
    status: str
    tier: str
    trust_score: float
    document_type: str | None = None
    document_number: str | None = None
    rejection_reason: str | None = None
    ocr_confidence: float | None = None


@router.post("/ocr")
async def run_ocr(
    id_front: UploadFile = File(...),
    id_back: UploadFile = File(...),
    utility_bill: UploadFile = File(...),
    session: DBSession = Depends(),
):
    """AI OCR extraction (Gemini). Stub implementation."""
    return {
        "success": True,
        "extracted": {
            "full_name": None,
            "date_of_birth": None,
            "id_number": None,
            "address": None,
        },
        "warnings": ["OCR not yet implemented"],
        "model_used": "gemini-2.0-flash",
    }


@router.post("/submit/{user_id}", response_model=KYCResponse)
async def submit_kyc(
    user_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Submit KYC application. Stub implementation."""
    return KYCResponse(
        id="stub-kyc-id",
        user_id=user_id,
        status="pending",
        tier="tier_0",
        trust_score=0.0,
    )


@router.get("/status/{user_id}", response_model=KYCResponse)
async def get_kyc_status(
    user_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Get KYC status. Stub implementation."""
    return KYCResponse(
        id="stub-kyc-id",
        user_id=user_id,
        status="pending",
        tier="tier_0",
        trust_score=0.0,
    )


@router.get("/submissions", response_model=List[KYCResponse])
async def list_kyc_submissions(
    session: DBSession,
    _: None = Depends(require_admin),
):
    """List all KYC submissions (admin). Stub implementation."""
    return []
