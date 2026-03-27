"""
Biometric API router.

Endpoints:
- POST /face/verify — Verify face
- POST /voice/verify — Verify voice
- GET /records — List user's biometric records
- GET /records/{id} — Get biometric record
- DELETE /records/{id} — Delete biometric record
- GET /submissions — [Admin] List all submissions
- POST /{id}/approve — [Admin] Approve biometric
- POST /{id}/reject — [Admin] Reject biometric
- POST /{id}/flag — [Admin] Flag as suspicious
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user_id, require_admin
from app.modules.biometric.application.use_cases.verify_face import VerifyFaceUseCase
from app.modules.biometric.application.use_cases.verify_voice import VerifyVoiceUseCase
from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.biometric.presentation.schemas.biometric_schemas import BiometricRecordResponse, BiometricRejectRequest
from app.modules.biometric.domain.entities.biometric_record import BiometricStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/biometric", tags=["biometric"])


@router.post("/face/verify", response_model=BiometricRecordResponse, status_code=201)
async def verify_face(
    face_image: UploadFile = File(...),
    id_photo: UploadFile | None = File(None),
    request: Request = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify face biometric.
    
    Upload face image (and optionally ID photo for matching).
    """
    repo = SQLAlchemyBiometricRepository(db)
    use_case = VerifyFaceUseCase(repo)
    
    face_bytes = await face_image.read()
    id_bytes = await id_photo.read() if id_photo else None
    
    device_info = {
        "user_agent": request.headers.get("user-agent") if request else None,
    }
    ip_address = request.client.host if request else None
    
    record = await use_case.execute(
        user_id=user_id,
        face_image_bytes=face_bytes,
        id_photo_bytes=id_bytes,
        device_info=device_info,
        ip_address=ip_address,
    )
    
    await db.commit()
    
    return BiometricRecordResponse(
        id=record.id,
        user_id=record.user_id,
        type=record.type.value,
        status=record.status.value,
        liveness_score=record.liveness_score,
        spoof_probability=record.spoof_probability,
        quality_score=record.quality_score,
        risk_level=record.risk_level.value,
        device_info=record.device_info,
        ip_address=record.ip_address,
        biometric_data_url=record.biometric_data_url,
        verified_at=record.verified_at,
        created_at=record.created_at,
    )


@router.post("/voice/verify", response_model=BiometricRecordResponse, status_code=201)
async def verify_voice(
    audio: UploadFile = File(...),
    request: Request = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify voice biometric.
    
    Upload voice sample (WAV, MP3, etc.).
    """
    repo = SQLAlchemyBiometricRepository(db)
    use_case = VerifyVoiceUseCase(repo)
    
    audio_bytes = await audio.read()
    
    device_info = {
        "user_agent": request.headers.get("user-agent") if request else None,
    }
    ip_address = request.client.host if request else None
    
    record = await use_case.execute(
        user_id=user_id,
        audio_bytes=audio_bytes,
        device_info=device_info,
        ip_address=ip_address,
    )
    
    await db.commit()
    
    return BiometricRecordResponse(
        id=record.id,
        user_id=record.user_id,
        type=record.type.value,
        status=record.status.value,
        liveness_score=record.liveness_score,
        spoof_probability=record.spoof_probability,
        quality_score=record.quality_score,
        risk_level=record.risk_level.value,
        device_info=record.device_info,
        ip_address=record.ip_address,
        biometric_data_url=record.biometric_data_url,
        verified_at=record.verified_at,
        created_at=record.created_at,
    )


@router.get("/records", response_model=List[BiometricRecordResponse])
async def list_my_records(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List user's biometric records."""
    repo = SQLAlchemyBiometricRepository(db)
    records = await repo.list_by_user(user_id)
    
    return [
        BiometricRecordResponse(
            id=r.id,
            user_id=r.user_id,
            type=r.type.value,
            status=r.status.value,
            liveness_score=r.liveness_score,
            spoof_probability=r.spoof_probability,
            quality_score=r.quality_score,
            risk_level=r.risk_level.value,
            device_info=r.device_info,
            ip_address=r.ip_address,
            biometric_data_url=r.biometric_data_url,
            verified_at=r.verified_at,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/records/{record_id}", response_model=BiometricRecordResponse)
async def get_record(
    record_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get biometric record details."""
    repo = SQLAlchemyBiometricRepository(db)
    record = await repo.get_by_id(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Biometric record not found")
    
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this record")
    
    return BiometricRecordResponse(
        id=record.id,
        user_id=record.user_id,
        type=record.type.value,
        status=record.status.value,
        liveness_score=record.liveness_score,
        spoof_probability=record.spoof_probability,
        quality_score=record.quality_score,
        risk_level=record.risk_level.value,
        device_info=record.device_info,
        ip_address=record.ip_address,
        biometric_data_url=record.biometric_data_url,
        verified_at=record.verified_at,
        created_at=record.created_at,
    )


@router.delete("/records/{record_id}", status_code=204)
async def delete_record(
    record_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete biometric record."""
    repo = SQLAlchemyBiometricRepository(db)
    record = await repo.get_by_id(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Biometric record not found")
    
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this record")
    
    await repo.delete(record_id)
    await db.commit()


@router.get("/submissions", response_model=List[BiometricRecordResponse], dependencies=[Depends(require_admin)])
async def list_all_submissions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] List all biometric submissions."""
    repo = SQLAlchemyBiometricRepository(db)
    records = await repo.list_all(skip=skip, limit=limit)
    
    return [
        BiometricRecordResponse(
            id=r.id,
            user_id=r.user_id,
            type=r.type.value,
            status=r.status.value,
            liveness_score=r.liveness_score,
            spoof_probability=r.spoof_probability,
            quality_score=r.quality_score,
            risk_level=r.risk_level.value,
            device_info=r.device_info,
            ip_address=r.ip_address,
            biometric_data_url=r.biometric_data_url,
            verified_at=r.verified_at,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post("/{record_id}/approve", response_model=BiometricRecordResponse, dependencies=[Depends(require_admin)])
async def approve_biometric(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Manually approve biometric record."""
    repo = SQLAlchemyBiometricRepository(db)
    record = await repo.get_by_id(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Biometric record not found")
    
    record.verify()
    updated = await repo.update(record)
    await db.commit()
    
    return BiometricRecordResponse(
        id=updated.id,
        user_id=updated.user_id,
        type=updated.type.value,
        status=updated.status.value,
        liveness_score=updated.liveness_score,
        spoof_probability=updated.spoof_probability,
        quality_score=updated.quality_score,
        risk_level=updated.risk_level.value,
        device_info=updated.device_info,
        ip_address=updated.ip_address,
        biometric_data_url=updated.biometric_data_url,
        verified_at=updated.verified_at,
        created_at=updated.created_at,
    )


@router.post("/{record_id}/reject", response_model=BiometricRecordResponse, dependencies=[Depends(require_admin)])
async def reject_biometric(
    record_id: str,
    body: BiometricRejectRequest,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Reject biometric record."""
    repo = SQLAlchemyBiometricRepository(db)
    record = await repo.get_by_id(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Biometric record not found")
    
    record.fail()
    updated = await repo.update(record)
    await db.commit()
    
    logger.info(f"Biometric {record_id} rejected: {body.reason}")
    
    return BiometricRecordResponse(
        id=updated.id,
        user_id=updated.user_id,
        type=updated.type.value,
        status=updated.status.value,
        liveness_score=updated.liveness_score,
        spoof_probability=updated.spoof_probability,
        quality_score=updated.quality_score,
        risk_level=updated.risk_level.value,
        device_info=updated.device_info,
        ip_address=updated.ip_address,
        biometric_data_url=updated.biometric_data_url,
        verified_at=updated.verified_at,
        created_at=updated.created_at,
    )


@router.post("/{record_id}/flag", response_model=BiometricRecordResponse, dependencies=[Depends(require_admin)])
async def flag_biometric(
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Flag biometric as suspicious."""
    repo = SQLAlchemyBiometricRepository(db)
    record = await repo.get_by_id(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Biometric record not found")
    
    record.flag()
    updated = await repo.update(record)
    await db.commit()
    
    return BiometricRecordResponse(
        id=updated.id,
        user_id=updated.user_id,
        type=updated.type.value,
        status=updated.status.value,
        liveness_score=updated.liveness_score,
        spoof_probability=updated.spoof_probability,
        quality_score=updated.quality_score,
        risk_level=updated.risk_level.value,
        device_info=updated.device_info,
        ip_address=updated.ip_address,
        biometric_data_url=updated.biometric_data_url,
        verified_at=updated.verified_at,
        created_at=updated.created_at,
    )
