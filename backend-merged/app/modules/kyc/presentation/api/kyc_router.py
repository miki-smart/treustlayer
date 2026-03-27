"""
KYC router � document submission and approval.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from app.api.dependencies import DBSession, CurrentUserId, require_admin, require_kyc_approver
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
