"""
eKYC router  — /api/v1/kyc/*

Endpoints:
  POST  /kyc/ocr                       Upload 3 documents → Gemini OCR → editable JSON
  POST  /kyc/submit/{user_id}          Submit KYC application (JSON body)
  GET   /kyc/status/{user_id}          Current KYC status for a user
  GET   /kyc/submissions               [Admin/KYC_Approver] list with user info
  POST  /kyc/{kyc_id}/approve          [Admin/KYC_Approver] approve
  POST  /kyc/{kyc_id}/reject           [Admin/KYC_Approver] reject
  GET   /kyc/applications              (legacy) list own applications
  GET   /kyc/applications/{app_id}     (legacy) get application detail
  POST  /kyc/applications              (legacy) submit via old schema
  PUT   /kyc/applications/{app_id}/review  (legacy) review
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentUser, AdminUser, DB
from app.schemas.kyc import KYCApplicationOut, KYCSubmitRequest, KYCReviewRequest
from app.schemas.ocr import OCRResponse, OCRExtractedData
from app.services import kyc_service, ocr_service
from app.config import settings
from app.models.user import UserRole, User
from app.models.kyc import KYCApplication, KYCStatus

router = APIRouter(prefix="/kyc", tags=["eKYC"])

_ALLOWED_MIME = {
    "image/jpeg", "image/jpg", "image/png",
    "image/webp", "image/tiff", "image/bmp",
    "application/pdf",
}
_MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB


# ── Shared output helpers ──────────────────────────────────────────────────────

class KYCResponseV2(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    user_email: str | None = None
    status: str
    tier: str
    trust_score: int
    document_type: str | None
    document_number: str | None
    rejection_reason: str | None
    face_similarity_score: float | None
    ocr_confidence: float | None = None
    submitted_at: str | None = None
    reviewed_at: str | None = None
    extracted_data: dict | None = None


def _kyc_v2_out(app: KYCApplication, user: User | None = None) -> KYCResponseV2:
    trust_score_map = {
        KYCStatus.pending:   10,
        KYCStatus.in_review: 20,
        KYCStatus.approved:  75,
        KYCStatus.rejected:   5,
        KYCStatus.flagged:    5,
    }
    return KYCResponseV2(
        id=str(app.id),
        user_id=str(app.user_id),
        user_name=user.name if user else (app.user.name if hasattr(app, "user") and app.user else None),
        user_email=user.email if user else (app.user.email if hasattr(app, "user") and app.user else None),
        status=str(app.status.value if hasattr(app.status, "value") else app.status),
        tier=getattr(app, "tier", "tier_0") or "tier_0",
        trust_score=trust_score_map.get(app.status, 10),
        document_type=getattr(app, "document_type", None),
        document_number=getattr(app, "document_number", None),
        rejection_reason=getattr(app, "rejection_reason", None) or app.notes,
        face_similarity_score=getattr(app, "face_similarity_score", None),
        ocr_confidence=app.ocr_confidence,
        submitted_at=app.submitted_at.isoformat() if app.submitted_at else None,
        reviewed_at=app.reviewed_at.isoformat() if app.reviewed_at else None,
        extracted_data=app.extracted_data,
    )


def _app_to_out(app, applicant_name, applicant_email, reviewer_name) -> KYCApplicationOut:
    return KYCApplicationOut(
        id=app.id,
        userId=str(app.user_id),
        applicantName=applicant_name,
        email=applicant_email,
        status=app.status,
        riskScore=app.risk_score,
        documentsSubmitted=app.documents_submitted,
        ocrConfidence=app.ocr_confidence,
        syntheticIdProbability=app.synthetic_id_probability,
        submittedAt=app.submitted_at.isoformat() if app.submitted_at else "",
        reviewedAt=app.reviewed_at.isoformat() if app.reviewed_at else None,
        reviewer=reviewer_name,
        notes=app.notes,
        extractedData=app.extracted_data,
    )


async def _read_and_validate(file: UploadFile, label: str) -> tuple[bytes, str]:
    mime = file.content_type or "application/octet-stream"
    if mime not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"{label}: unsupported type '{mime}'. Accepted: JPEG, PNG, WebP, TIFF, BMP, PDF.",
        )
    data = await file.read()
    if len(data) > _MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"{label}: exceeds 20 MB limit.")
    if not data:
        raise HTTPException(status_code=422, detail=f"{label}: file is empty.")
    return data, mime


# ── OCR endpoint ──────────────────────────────────────────────────────────────

@router.post("/ocr", response_model=OCRResponse, summary="Upload documents and extract data via Gemini OCR")
async def ocr_documents(
    current_user: CurrentUser,
    id_front: UploadFile = File(..., description="National ID — front side"),
    id_back: UploadFile = File(..., description="National ID — back side"),
    utility_bill: UploadFile = File(..., description="Utility bill / proof of address"),
):
    """
    Upload three documents → Gemini AI extracts identity fields → return for user review.
    If GEMINI_API_KEY is not set, returns a clearly-labeled demo response.
    """
    front_bytes, front_mime = await _read_and_validate(id_front, "National ID front")
    back_bytes, back_mime = await _read_and_validate(id_back, "National ID back")
    util_bytes, util_mime = await _read_and_validate(utility_bill, "Utility Bill")

    no_key = not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here"
    if no_key:
        # Return a realistic demo response so the wizard still works end-to-end
        return OCRResponse(
            success=True,
            extracted=OCRExtractedData(
                full_name="[Demo] Abebe Kebede",
                date_of_birth="1990-05-12",
                id_number="ETH-2019-DEMO001",
                gender="Male",
                nationality="Ethiopian",
                place_of_birth="Addis Ababa",
                issue_date="2019-06-01",
                expiry_date="2029-06-01",
                address="Bole Sub-City, Woreda 03, Addis Ababa, Ethiopia",
                billing_name="[Demo] Abebe Kebede",
                service_provider="Ethiopian Electric Utility",
                service_type="electricity",
                bill_date="2026-02-15",
                account_number="EEU-ACC-0012345",
                mrz_line1="IDETH0000000001<<<<<<<<<<<<<<<",
                mrz_line2="9005120M2906011ETH<<<<<<<<<<<6",
                id_ocr_confidence=0.0,
                utility_ocr_confidence=0.0,
                overall_confidence=0.0,
                documents_processed=["National ID (front)", "National ID (back)", "Utility Bill"],
            ),
            warnings=[
                "⚠ GEMINI_API_KEY is not set — this is a DEMO response, not real OCR.",
                "Set GEMINI_API_KEY in your .env to enable real AI document extraction.",
            ],
            model_used="demo-mode",
        )

    warnings: list[str] = []
    try:
        extracted = await ocr_service.extract_documents(
            id_front_bytes=front_bytes, id_front_mime=front_mime,
            id_back_bytes=back_bytes, id_back_mime=back_mime,
            utility_bytes=util_bytes, utility_mime=util_mime,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if not extracted.full_name:
        warnings.append("Could not extract full name from National ID.")
    if not extracted.id_number:
        warnings.append("Could not extract ID number from National ID.")
    if not extracted.address:
        warnings.append("Could not extract address from Utility Bill or National ID.")
    if extracted.overall_confidence < 0.6:
        warnings.append("Low OCR confidence — please verify all fields carefully.")

    return OCRResponse(
        success=True,
        extracted=extracted,
        warnings=warnings,
        model_used=settings.GEMINI_MODEL,
    )


# ── TrustLayer ID spec routes ─────────────────────────────────────────────────

class KYCSubmitRequestV2(BaseModel):
    document_type: str
    document_number: str
    document_url: str | None = None
    face_image_url: str | None = None
    extracted_data: dict | None = None


@router.post("/submit/{user_id}", response_model=KYCResponseV2, status_code=202, summary="Submit KYC documents for a user")
async def submit_kyc(user_id: str, body: KYCSubmitRequestV2, current_user: CurrentUser, db: DB):
    uid = uuid.UUID(user_id)
    if str(current_user.id) != user_id and current_user.role not in (UserRole.admin, UserRole.kyc_approver):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check for existing pending/in_review application — prevent duplicates
    existing = (await db.execute(
        select(KYCApplication)
        .where(KYCApplication.user_id == uid, KYCApplication.status.in_([KYCStatus.pending, KYCStatus.in_review]))
        .order_by(KYCApplication.submitted_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    if existing:
        return _kyc_v2_out(existing, current_user)

    ocr_conf = 0.0
    if body.extracted_data and body.extracted_data.get("overall_confidence"):
        ocr_conf = float(body.extracted_data["overall_confidence"])

    app = KYCApplication(
        id=uuid.uuid4(),
        user_id=uid,
        status=KYCStatus.pending,
        risk_score=max(10, int((1.0 - ocr_conf) * 50)) if ocr_conf > 0 else 30,
        documents_submitted=[body.document_type],
        ocr_confidence=ocr_conf,
        synthetic_id_probability=0.05,
        document_type=body.document_type,
        document_number=body.document_number,
        document_url=body.document_url or "",
        face_image_url=body.face_image_url,
        tier="tier_1",
        face_similarity_score=None,
        extracted_data=body.extracted_data,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(app)
    await db.flush()
    return _kyc_v2_out(app, current_user)


@router.get("/status/{user_id}", response_model=KYCResponseV2, summary="Get KYC status for a user")
async def get_kyc_status(user_id: str, current_user: CurrentUser, db: DB):
    if str(current_user.id) != user_id and current_user.role not in (UserRole.admin, UserRole.kyc_approver):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(KYCApplication)
        .where(KYCApplication.user_id == uuid.UUID(user_id))
        .order_by(KYCApplication.submitted_at.desc())
        .limit(1)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="No KYC application found for this user")
    return _kyc_v2_out(app)


@router.get("/submissions", response_model=list[KYCResponseV2], summary="[Admin/KYC_Approver] List KYC submissions with user info")
async def list_kyc_submissions(
    current_user: CurrentUser, db: DB,
    kyc_status: str = Query(default="all", description="Filter: all | pending | in_review | approved | rejected | flagged"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    if current_user.role not in (UserRole.admin, UserRole.kyc_approver):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    q = (
        select(KYCApplication)
        .options(selectinload(KYCApplication.user))
        .order_by(KYCApplication.submitted_at.desc())
        .offset(skip).limit(limit)
    )
    if kyc_status != "all":
        try:
            q = q.where(KYCApplication.status == KYCStatus(kyc_status))
        except ValueError:
            pass

    result = await db.execute(q)
    return [_kyc_v2_out(a) for a in result.scalars().all()]


@router.post("/{kyc_id}/approve", response_model=KYCResponseV2, summary="Approve a KYC submission")
async def approve_kyc(kyc_id: str, current_user: CurrentUser, db: DB):
    if current_user.role not in (UserRole.admin, UserRole.kyc_approver):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    app = await kyc_service.get_application_by_id(db, uuid.UUID(kyc_id))
    app.status = KYCStatus.approved
    app.tier = "tier_2"
    app.reviewer_id = current_user.id
    app.reviewed_at = datetime.now(timezone.utc)
    # Recalculate trust profile
    from app.services import trust_service
    user_r = await db.execute(select(User).where(User.id == app.user_id))
    user = user_r.scalar_one_or_none()
    if user:
        await trust_service.evaluate_trust(db, user)
    return _kyc_v2_out(app)


class KYCRejectRequestV2(BaseModel):
    reason: str


@router.post("/{kyc_id}/reject", response_model=KYCResponseV2, summary="Reject a KYC submission")
async def reject_kyc(kyc_id: str, body: KYCRejectRequestV2, current_user: CurrentUser, db: DB):
    if current_user.role not in (UserRole.admin, UserRole.kyc_approver):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    app = await kyc_service.get_application_by_id(db, uuid.UUID(kyc_id))
    app.status = KYCStatus.rejected
    app.rejection_reason = body.reason
    app.notes = body.reason
    app.reviewer_id = current_user.id
    app.reviewed_at = datetime.now(timezone.utc)
    return _kyc_v2_out(app)


@router.delete("/{kyc_id}", status_code=204, summary="[Admin] Permanently delete a KYC submission")
async def delete_kyc(kyc_id: str, current_user: CurrentUser, db: DB):
    if current_user.role not in (UserRole.admin,):
        raise HTTPException(status_code=403, detail="Only admins can delete KYC records")
    app = await kyc_service.get_application_by_id(db, uuid.UUID(kyc_id))
    await db.delete(app)
    await db.flush()


@router.post("/{kyc_id}/flag", response_model=KYCResponseV2, summary="Flag a KYC submission for further review")
async def flag_kyc(kyc_id: str, body: KYCRejectRequestV2, current_user: CurrentUser, db: DB):
    if current_user.role not in (UserRole.admin, UserRole.kyc_approver):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    app = await kyc_service.get_application_by_id(db, uuid.UUID(kyc_id))
    app.status = KYCStatus.flagged
    app.notes = body.reason
    app.reviewer_id = current_user.id
    app.reviewed_at = datetime.now(timezone.utc)
    return _kyc_v2_out(app)


# ── Legacy routes (keep for backward compat) ─────────────────────────────────

@router.get("/applications", response_model=list[KYCApplicationOut])
async def list_applications(current_user: CurrentUser, db: DB):
    is_admin = current_user.role in (UserRole.admin, UserRole.kyc_approver)
    apps = await kyc_service.get_applications(db, current_user, is_admin)
    return [
        _app_to_out(a,
                    a.user.name if a.user else str(a.user_id),
                    a.user.email if a.user else "",
                    a.reviewer.name if a.reviewer else None)
        for a in apps
    ]


@router.get("/applications/{app_id}", response_model=KYCApplicationOut)
async def get_application(app_id: uuid.UUID, current_user: CurrentUser, db: DB):
    app = await kyc_service.get_application_by_id(db, app_id)
    if current_user.role not in (UserRole.admin, UserRole.kyc_approver) and app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _app_to_out(app,
                       app.user.name if app.user else str(app.user_id),
                       app.user.email if app.user else "",
                       app.reviewer.name if app.reviewer else None)


@router.post("/applications", response_model=KYCApplicationOut, status_code=201)
async def submit_application(body: KYCSubmitRequest, current_user: CurrentUser, db: DB):
    app = await kyc_service.submit_application(db, current_user, body.documents_submitted, body.extracted_data)
    return _app_to_out(app, current_user.name, current_user.email, None)


@router.put("/applications/{app_id}/review", response_model=KYCApplicationOut)
async def review_application(app_id: uuid.UUID, body: KYCReviewRequest, current_user: AdminUser, db: DB):
    app = await kyc_service.review_application(db, app_id, current_user, body.status, body.notes)
    return _app_to_out(app,
                       app.user.name if app.user else str(app.user_id),
                       app.user.email if app.user else "",
                       app.reviewer.name if app.reviewer else current_user.name)
