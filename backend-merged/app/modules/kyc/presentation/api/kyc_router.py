"""
KYC router — document submission and approval.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from app.core.config import settings
from app.api.dependencies import DBSession, CurrentUserId, require_kyc_approver
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.application.services.file_storage_service import FileStorageService
from app.modules.kyc.application.services.ocr_service import OCRService
from app.modules.kyc.application.use_cases.submit_kyc import SubmitKYCUseCase
from app.modules.kyc.application.use_cases.approve_kyc import ApproveKYCUseCase
from app.modules.kyc.application.use_cases.reject_kyc import RejectKYCUseCase
from app.modules.kyc.application.use_cases.list_kyc_queue import ListKYCQueueUseCase
from app.modules.kyc.domain.entities.kyc_verification import KYCStatus, KYCTier

router = APIRouter()


class OcrExtractedData(BaseModel):
    """Merged ID + utility fields for the eKYC wizard (matches frontend OcrExtractedData)."""

    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    id_number: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    place_of_birth: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    address: Optional[str] = None
    billing_name: Optional[str] = None
    service_provider: Optional[str] = None
    service_type: Optional[str] = None
    bill_date: Optional[str] = None
    account_number: Optional[str] = None
    mrz_line1: Optional[str] = None
    mrz_line2: Optional[str] = None
    id_ocr_confidence: float = 0.0
    utility_ocr_confidence: float = 0.0
    overall_confidence: float = 0.0
    documents_processed: List[str] = Field(default_factory=list)


class OcrRunResponse(BaseModel):
    success: bool
    extracted: OcrExtractedData
    warnings: List[str]
    model_used: str


class KYCResponse(BaseModel):
    id: str
    user_id: str
    status: str
    tier: str
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    address: Optional[str] = None
    id_front_url: Optional[str] = None
    id_back_url: Optional[str] = None
    utility_bill_url: Optional[str] = None
    face_image_url: Optional[str] = None
    overall_confidence: float
    risk_score: int
    rejection_reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None


def _merge_ocr_to_extracted(
    id_data: dict,
    utility_data: dict,
    id_conf: float,
    util_conf: float,
    had_id_back: bool,
) -> OcrExtractedData:
    """Normalize Gemini JSON blobs into the shape expected by the SPA."""
    id_data = dict(id_data or {})
    utility_data = dict(utility_data or {})
    id_data.pop("confidence", None)
    utility_data.pop("confidence", None)

    overall = (float(id_conf) + float(util_conf)) / 2.0 if (id_conf or util_conf) else 0.0
    docs = ["id_front"] + (["id_back"] if had_id_back else []) + ["utility_bill"]

    return OcrExtractedData(
        full_name=id_data.get("full_name"),
        date_of_birth=id_data.get("date_of_birth") if isinstance(id_data.get("date_of_birth"), str) else None,
        id_number=id_data.get("document_number"),
        gender=id_data.get("gender"),
        nationality=id_data.get("nationality"),
        place_of_birth=id_data.get("place_of_birth"),
        issue_date=id_data.get("issue_date") if isinstance(id_data.get("issue_date"), str) else None,
        expiry_date=id_data.get("expiry_date") if isinstance(id_data.get("expiry_date"), str) else None,
        address=utility_data.get("address"),
        billing_name=utility_data.get("billing_name"),
        service_provider=utility_data.get("service_provider"),
        service_type=utility_data.get("service_type"),
        bill_date=utility_data.get("bill_date") if isinstance(utility_data.get("bill_date"), str) else None,
        account_number=utility_data.get("account_number"),
        mrz_line1=id_data.get("mrz_line1"),
        mrz_line2=id_data.get("mrz_line2"),
        id_ocr_confidence=float(id_conf or 0.0),
        utility_ocr_confidence=float(util_conf or 0.0),
        overall_confidence=overall,
        documents_processed=docs,
    )


@router.post("/ocr", response_model=OcrRunResponse)
async def run_kyc_ocr(
    session: DBSession,
    current_user_id: CurrentUserId,
    id_front: UploadFile = File(...),
    id_back: UploadFile | None = File(None),
    utility_bill: UploadFile = File(...),
):
    """
    Run OCR only (no DB write, no face image). Used by the eKYC wizard before review/submit.
    """
    _ = session  # auth / dependency wiring; no persistence here
    _ = current_user_id

    id_front_bytes = await id_front.read()
    id_back_bytes = await id_back.read() if id_back else None
    utility_bill_bytes = await utility_bill.read()

    ocr_service = OCRService()
    id_ocr_result = await ocr_service.extract_id_document(id_front_bytes, id_back_bytes)
    utility_ocr_result = await ocr_service.extract_utility_bill(utility_bill_bytes)

    id_data = id_ocr_result.get("extracted") or {}
    utility_data = utility_ocr_result.get("extracted") or {}
    id_conf = float(id_ocr_result.get("confidence") or 0.0)
    util_conf = float(utility_ocr_result.get("confidence") or 0.0)

    warnings: List[str] = []
    if not settings.GEMINI_API_KEY and not settings.GEMINI_OCR_MOCK:
        warnings.append("GEMINI_API_KEY is not set; OCR returned empty placeholders.")
    warnings.extend(id_ocr_result.get("warnings") or [])
    warnings.extend(utility_ocr_result.get("warnings") or [])
    if id_ocr_result.get("error"):
        warnings.append(f"ID OCR: {id_ocr_result['error']}")
    if utility_ocr_result.get("error"):
        warnings.append(f"Utility bill OCR: {utility_ocr_result['error']}")

    extracted = _merge_ocr_to_extracted(
        id_data,
        utility_data,
        id_conf,
        util_conf,
        had_id_back=bool(id_back_bytes),
    )
    success = bool(id_ocr_result.get("success")) and bool(utility_ocr_result.get("success"))
    if settings.GEMINI_OCR_MOCK:
        model_used = "mock"
    elif not settings.GEMINI_API_KEY:
        model_used = "disabled"
    else:
        model_used = settings.GEMINI_MODEL

    return OcrRunResponse(
        success=success,
        extracted=extracted,
        warnings=warnings,
        model_used=model_used,
    )


@router.post("/submit", response_model=KYCResponse)
async def submit_kyc(
    session: DBSession,
    current_user_id: CurrentUserId,
    id_front: UploadFile = File(...),
    id_back: UploadFile = File(None),
    utility_bill: UploadFile = File(...),
    face_image: UploadFile = File(...),
):
    """
    Submit KYC documents for verification.
    
    Uploads:
    - id_front: Front of ID document (required)
    - id_back: Back of ID document (optional)
    - utility_bill: Utility bill for address proof (required)
    - face_image: Face photo (required)
    """
    kyc_repo = SQLAlchemyKYCRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    file_storage = FileStorageService()
    ocr_service = OCRService()
    
    use_case = SubmitKYCUseCase(kyc_repo, user_repo, file_storage, ocr_service)
    
    id_front_bytes = await id_front.read()
    id_back_bytes = await id_back.read() if id_back else None
    utility_bill_bytes = await utility_bill.read()
    face_image_bytes = await face_image.read()
    
    kyc = await use_case.execute(
        user_id=current_user_id,
        id_front_bytes=id_front_bytes,
        id_back_bytes=id_back_bytes,
        utility_bill_bytes=utility_bill_bytes,
        face_image_bytes=face_image_bytes,
    )
    
    await session.commit()
    
    return KYCResponse(
        id=kyc.id,
        user_id=kyc.user_id,
        status=kyc.status.value,
        tier=kyc.tier.value,
        full_name=kyc.full_name,
        date_of_birth=kyc.date_of_birth,
        document_type=kyc.document_type,
        document_number=kyc.document_number,
        address=kyc.address,
        id_front_url=kyc.id_front_url,
        id_back_url=kyc.id_back_url,
        utility_bill_url=kyc.utility_bill_url,
        face_image_url=kyc.face_image_url,
        overall_confidence=kyc.overall_confidence,
        risk_score=kyc.risk_score,
        rejection_reason=kyc.rejection_reason,
        reviewer_id=kyc.reviewer_id,
        submitted_at=kyc.submitted_at.isoformat() if kyc.submitted_at else None,
        reviewed_at=kyc.reviewed_at.isoformat() if kyc.reviewed_at else None,
    )


@router.get("/status", response_model=KYCResponse)
async def get_kyc_status(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """Get current user's KYC status."""
    kyc_repo = SQLAlchemyKYCRepository(session)
    kyc = await kyc_repo.get_by_user_id(current_user_id)
    
    if not kyc:
        raise HTTPException(status_code=404, detail="No KYC submission found")
    
    return KYCResponse(
        id=kyc.id,
        user_id=kyc.user_id,
        status=kyc.status.value,
        tier=kyc.tier.value,
        full_name=kyc.full_name,
        date_of_birth=kyc.date_of_birth,
        document_type=kyc.document_type,
        document_number=kyc.document_number,
        address=kyc.address,
        id_front_url=kyc.id_front_url,
        id_back_url=kyc.id_back_url,
        utility_bill_url=kyc.utility_bill_url,
        face_image_url=kyc.face_image_url,
        overall_confidence=kyc.overall_confidence,
        risk_score=kyc.risk_score,
        rejection_reason=kyc.rejection_reason,
        reviewer_id=kyc.reviewer_id,
        submitted_at=kyc.submitted_at.isoformat() if kyc.submitted_at else None,
        reviewed_at=kyc.reviewed_at.isoformat() if kyc.reviewed_at else None,
    )


@router.get("/queue", response_model=List[KYCResponse])
async def list_kyc_queue(
    session: DBSession,
    _: None = Depends(require_kyc_approver),
    status: Optional[str] = "pending",
    skip: int = 0,
    limit: int = 50,
):
    """
    List KYC submissions in review queue.
    
    Only accessible by KYC approvers and admins.
    """
    kyc_repo = SQLAlchemyKYCRepository(session)
    use_case = ListKYCQueueUseCase(kyc_repo)
    
    kyc_status = KYCStatus(status) if status else KYCStatus.PENDING
    verifications = await use_case.execute(kyc_status, skip, limit)
    
    return [
        KYCResponse(
            id=kyc.id,
            user_id=kyc.user_id,
            status=kyc.status.value,
            tier=kyc.tier.value,
            full_name=kyc.full_name,
            date_of_birth=kyc.date_of_birth,
            document_type=kyc.document_type,
            document_number=kyc.document_number,
            address=kyc.address,
            id_front_url=kyc.id_front_url,
            id_back_url=kyc.id_back_url,
            utility_bill_url=kyc.utility_bill_url,
            face_image_url=kyc.face_image_url,
            overall_confidence=kyc.overall_confidence,
            risk_score=kyc.risk_score,
            rejection_reason=kyc.rejection_reason,
            reviewer_id=kyc.reviewer_id,
            submitted_at=kyc.submitted_at.isoformat() if kyc.submitted_at else None,
            reviewed_at=kyc.reviewed_at.isoformat() if kyc.reviewed_at else None,
        )
        for kyc in verifications
    ]


class ApproveKYCRequest(BaseModel):
    tier: str
    notes: Optional[str] = None


@router.post("/approve/{verification_id}", response_model=KYCResponse)
async def approve_kyc(
    verification_id: str,
    payload: ApproveKYCRequest,
    session: DBSession,
    current_user_id: CurrentUserId,
    _: None = Depends(require_kyc_approver),
):
    """
    Approve KYC verification.
    
    Only accessible by KYC approvers and admins.
    """
    kyc_repo = SQLAlchemyKYCRepository(session)
    use_case = ApproveKYCUseCase(kyc_repo)
    
    tier = KYCTier(payload.tier)
    kyc = await use_case.execute(verification_id, current_user_id, tier, payload.notes)
    
    await session.commit()
    
    return KYCResponse(
        id=kyc.id,
        user_id=kyc.user_id,
        status=kyc.status.value,
        tier=kyc.tier.value,
        full_name=kyc.full_name,
        date_of_birth=kyc.date_of_birth,
        document_type=kyc.document_type,
        document_number=kyc.document_number,
        address=kyc.address,
        id_front_url=kyc.id_front_url,
        id_back_url=kyc.id_back_url,
        utility_bill_url=kyc.utility_bill_url,
        face_image_url=kyc.face_image_url,
        overall_confidence=kyc.overall_confidence,
        risk_score=kyc.risk_score,
        rejection_reason=kyc.rejection_reason,
        reviewer_id=kyc.reviewer_id,
        submitted_at=kyc.submitted_at.isoformat() if kyc.submitted_at else None,
        reviewed_at=kyc.reviewed_at.isoformat() if kyc.reviewed_at else None,
    )


class RejectKYCRequest(BaseModel):
    reason: str


@router.post("/reject/{verification_id}", response_model=KYCResponse)
async def reject_kyc(
    verification_id: str,
    payload: RejectKYCRequest,
    session: DBSession,
    current_user_id: CurrentUserId,
    _: None = Depends(require_kyc_approver),
):
    """
    Reject KYC verification.
    
    Only accessible by KYC approvers and admins.
    """
    kyc_repo = SQLAlchemyKYCRepository(session)
    use_case = RejectKYCUseCase(kyc_repo)
    
    kyc = await use_case.execute(verification_id, current_user_id, payload.reason)
    
    await session.commit()
    
    return KYCResponse(
        id=kyc.id,
        user_id=kyc.user_id,
        status=kyc.status.value,
        tier=kyc.tier.value,
        full_name=kyc.full_name,
        date_of_birth=kyc.date_of_birth,
        document_type=kyc.document_type,
        document_number=kyc.document_number,
        address=kyc.address,
        id_front_url=kyc.id_front_url,
        id_back_url=kyc.id_back_url,
        utility_bill_url=kyc.utility_bill_url,
        face_image_url=kyc.face_image_url,
        overall_confidence=kyc.overall_confidence,
        risk_score=kyc.risk_score,
        rejection_reason=kyc.rejection_reason,
        reviewer_id=kyc.reviewer_id,
        submitted_at=kyc.submitted_at.isoformat() if kyc.submitted_at else None,
        reviewed_at=kyc.reviewed_at.isoformat() if kyc.reviewed_at else None,
    )
