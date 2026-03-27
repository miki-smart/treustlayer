from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role
from app.core.database import get_async_session
from app.core.exceptions import InvalidOperationError, NotFoundError
from app.modules.identity.domain.entities.user import UserRole
from app.modules.kyc.application.dto.kyc_dto import SubmitKYCDTO
from app.modules.kyc.application.use_cases.kyc_use_cases import (
    ApproveKYCUseCase,
    RejectKYCUseCase,
    SubmitKYCUseCase,
)
from app.modules.kyc.domain.entities.kyc_verification import KYCStatus
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.kyc.presentation.schemas.kyc_schemas import (
    KYCRejectRequest,
    KYCResponse,
    KYCSubmitRequest,
)

router = APIRouter(prefix="/kyc", tags=["KYC"])


def _repo(session: AsyncSession) -> SQLAlchemyKYCRepository:
    return SQLAlchemyKYCRepository(session)


def _to_response(entity) -> KYCResponse:
    return KYCResponse(
        id=entity.id,
        user_id=entity.user_id,
        status=entity.status.value,
        tier=entity.tier.value,
        trust_score=entity.trust_score,
        document_type=entity.document_type,
        document_number=entity.document_number,
        rejection_reason=entity.rejection_reason,
        face_similarity_score=entity.face_similarity_score,
    )


@router.post(
    "/submit/{user_id}",
    response_model=KYCResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit KYC documents for a user",
)
async def submit_kyc(
    user_id: str,
    payload: KYCSubmitRequest,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = SubmitKYCUseCase(_repo(session))
    try:
        result = await use_case.execute(
            SubmitKYCDTO(
                user_id=user_id,
                document_type=payload.document_type,
                document_number=payload.document_number,
                document_url=payload.document_url,
                face_image_url=payload.face_image_url,
            )
        )
        await session.commit()
        return KYCResponse(**result.__dict__)
    except InvalidOperationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/{kyc_id}/approve",
    response_model=KYCResponse,
    summary="Approve a KYC submission (admin/kyc_approver)",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.KYC_APPROVER))],
)
async def approve_kyc(
    kyc_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = ApproveKYCUseCase(_repo(session))
    try:
        result = await use_case.execute(kyc_id)
        await session.commit()
        return KYCResponse(**result.__dict__)
    except (NotFoundError, InvalidOperationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc))


@router.post(
    "/{kyc_id}/reject",
    response_model=KYCResponse,
    summary="Reject a KYC submission (admin/kyc_approver)",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.KYC_APPROVER))],
)
async def reject_kyc(
    kyc_id: str,
    payload: KYCRejectRequest,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = RejectKYCUseCase(_repo(session))
    try:
        result = await use_case.execute(kyc_id, payload.reason)
        await session.commit()
        return KYCResponse(**result.__dict__)
    except (NotFoundError, InvalidOperationError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc))


@router.get(
    "/status/{user_id}",
    response_model=KYCResponse,
    summary="Get KYC status for a user",
)
async def get_kyc_status(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    entity = await _repo(session).get_by_user_id(user_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No KYC record found")
    return _to_response(entity)


@router.get(
    "/submissions",
    response_model=List[KYCResponse],
    summary="[Admin/KYC_Approver] List KYC submissions, optionally filter by status",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.KYC_APPROVER))],
)
async def list_kyc_submissions(
    kyc_status: str = Query(
        default="submitted",
        description="Filter by status: pending, submitted, approved, rejected",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        status_enum = KYCStatus(kyc_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{kyc_status}'. Must be one of: {[s.value for s in KYCStatus]}",
        )
    results = await _repo(session).list_by_status(status_enum, skip=skip, limit=limit)
    return [_to_response(r) for r in results]
