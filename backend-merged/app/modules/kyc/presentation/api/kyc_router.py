"""
KYC router — document submission and approval.
"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from datetime import date

from app.core.config import settings
from app.api.dependencies import DBSession, CurrentUserId, require_kyc_approver
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.application.services.file_storage_service import FileStorageService
from app.modules.kyc.application.services.ocr_merge import average_id_confidence, merge_id_front_back
from app.modules.kyc.application.services.ocr_service import OCRService
from app.modules.kyc.application.use_cases.submit_kyc import SubmitKYCUseCase
from app.modules.kyc.application.use_cases.approve_kyc import ApproveKYCUseCase
from app.modules.kyc.application.use_cases.reject_kyc import RejectKYCUseCase
from app.modules.kyc.application.use_cases.list_kyc_queue import ListKYCQueueUseCase
from app.modules.kyc.domain.entities.kyc_verification import KYCStatus, KYCTier
from app.modules.identity.presentation.schemas.user_schemas import UserResponse
from app.modules.trust.application.use_cases.recalculate_trust_for_user import RecalculateTrustForUserUseCase
from app.modules.trust.integration.recalculate_trust import recalculate_trust_for_user_session
from app.modules.trust.presentation.helpers.trust_profile_response import build_trust_profile_response
from app.modules.trust.presentation.schemas.trust_schemas import TrustProfileResponse
from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.digital_identity.infrastructure.persistence.identity_repository_impl import SQLAlchemyDigitalIdentityRepository
from app.modules.trust.infrastructure.persistence.trust_repository_impl import SQLAlchemyTrustRepository

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
    """Merged ID + utility fields (wizard summary)."""
    id_front: Dict[str, Any] = Field(default_factory=dict)
    id_back: Dict[str, Any] = Field(default_factory=dict)
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
    extracted_data: Optional[Dict[str, Any]] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    trust_score: Optional[float] = None


class KycApproverUserDetailResponse(BaseModel):
    user: UserResponse
    kyc: Optional[KYCResponse] = None
    trust: TrustProfileResponse


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
    front_res = await ocr_service.extract_id_front(id_front_bytes)
    back_res = (
        await ocr_service.extract_id_back(id_back_bytes)
        if id_back_bytes
        else {"success": True, "extracted": {}, "confidence": 0.0}
    )
    utility_ocr_result = await ocr_service.extract_utility_bill(utility_bill_bytes)

    fe = dict(front_res.get("extracted") or {})
    be = dict(back_res.get("extracted") or {})
    utility_data = dict(utility_ocr_result.get("extracted") or {})
    id_merge = merge_id_front_back(fe, be)
    id_conf = average_id_confidence(
        float(front_res.get("confidence") or 0.0),
        float(back_res.get("confidence") or 0.0) if id_back_bytes else None,
        bool(id_back_bytes),
    )
    util_conf = float(utility_ocr_result.get("confidence") or 0.0)

    warnings: List[str] = []
    if not settings.GEMINI_API_KEY and not settings.GEMINI_OCR_MOCK:
        warnings.append("GEMINI_API_KEY is not set; OCR returned empty placeholders.")
    warnings.extend(front_res.get("warnings") or [])
    warnings.extend(back_res.get("warnings") or [])
    warnings.extend(utility_ocr_result.get("warnings") or [])
    if front_res.get("error"):
        warnings.append(f"ID front OCR: {front_res['error']}")
    if id_back_bytes and back_res.get("error"):
        warnings.append(f"ID back OCR: {back_res['error']}")
    if utility_ocr_result.get("error"):
        warnings.append(f"Utility bill OCR: {utility_ocr_result['error']}")

    extracted = _merge_ocr_to_extracted(
        id_merge,
        utility_data,
        id_conf,
        util_conf,
        had_id_back=bool(id_back_bytes),
    )
    success = bool(front_res.get("success")) and bool(utility_ocr_result.get("success"))
    if id_back_bytes:
        success = success and bool(back_res.get("success"))
    if settings.GEMINI_OCR_MOCK:
        model_used = "mock"
    elif not settings.GEMINI_API_KEY:
        model_used = "disabled"
    else:
        model_used = settings.GEMINI_MODEL

    return OcrRunResponse(
        success=success,
        extracted=extracted,
        id_front=fe,
        id_back=be,
        warnings=warnings,
        model_used=model_used,
    )


def _kyc_to_response(kyc, **extra: Any) -> KYCResponse:
    base = dict(
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
        extracted_data=kyc.extracted_data,
    )
    base.update(extra)
    return KYCResponse(**base)


@router.post("/submit", response_model=KYCResponse)
async def submit_kyc(
    session: DBSession,
    current_user_id: CurrentUserId,
    id_front: UploadFile = File(...),
    id_back: UploadFile = File(None),
    utility_bill: UploadFile = File(...),
    face_image: UploadFile = File(...),
    kyc_overrides: Optional[str] = Form(None),
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

    overrides: Optional[Dict[str, Any]] = None
    if kyc_overrides:
        try:
            overrides = json.loads(kyc_overrides)
            if not isinstance(overrides, dict):
                overrides = None
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid kyc_overrides JSON")

    kyc = await use_case.execute(
        user_id=current_user_id,
        id_front_bytes=id_front_bytes,
        id_back_bytes=id_back_bytes,
        utility_bill_bytes=utility_bill_bytes,
        face_image_bytes=face_image_bytes,
        overrides=overrides,
    )

    await session.commit()

    return _kyc_to_response(kyc)


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

    return _kyc_to_response(kyc)


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
    
    return [_kyc_to_response(k) for k in verifications]


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

    await recalculate_trust_for_user_session(session, kyc.user_id)
    await session.commit()

    return _kyc_to_response(kyc)


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

    await recalculate_trust_for_user_session(session, kyc.user_id)
    await session.commit()

    return _kyc_to_response(kyc)


@router.get(
    "/approver/users/{user_id}/detail",
    response_model=KycApproverUserDetailResponse,
    summary="User + KYC + trust for KYC approver",
)
async def get_approver_user_detail(
    user_id: str,
    session: DBSession,
    _: None = Depends(require_kyc_approver),
):
    user_repo = SQLAlchemyUserRepository(session)
    kyc_repo = SQLAlchemyKYCRepository(session)
    trust_repo = SQLAlchemyTrustRepository(session)
    biometric_repo = SQLAlchemyBiometricRepository(session)
    identity_repo = SQLAlchemyDigitalIdentityRepository(session)

    user_entity = await user_repo.get_by_id(user_id)
    if not user_entity:
        raise HTTPException(status_code=404, detail="User not found")

    user_resp = UserResponse(
        id=user_entity.id,
        email=user_entity.email,
        username=user_entity.username,
        role=user_entity.role.value,
        full_name=user_entity.full_name,
        phone_number=user_entity.phone_number,
        avatar=user_entity.avatar,
        is_active=user_entity.is_active,
        is_email_verified=user_entity.is_email_verified,
        phone_verified=user_entity.phone_verified,
        created_at=user_entity.created_at,
    )

    kyc = await kyc_repo.get_by_user_id(user_id)
    kyc_resp: Optional[KYCResponse] = _kyc_to_response(kyc) if kyc else None

    recalc = RecalculateTrustForUserUseCase(
        trust_repo, user_repo, kyc_repo, biometric_repo, identity_repo
    )
    profile = await recalc.execute(user_id)
    await session.commit()

    trust_resp = build_trust_profile_response(profile, user_entity)
    return KycApproverUserDetailResponse(user=user_resp, kyc=kyc_resp, trust=trust_resp)
