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
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user_id, require_admin
from app.modules.biometric.application.use_cases.verify_face import VerifyFaceUseCase
from app.modules.biometric.application.use_cases.verify_voice import VerifyVoiceUseCase
from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.biometric.presentation.schemas.biometric_schemas import BiometricRecordResponse, BiometricRejectRequest
from app.modules.trust.integration.recalculate_trust import recalculate_trust_for_user_session

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FACE_BYTES = 10 * 1024 * 1024
MAX_VOICE_BYTES = 20 * 1024 * 1024


def _record_to_response(record) -> BiometricRecordResponse:
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


def _validate_image_bytes(data: bytes, content_type: Optional[str]) -> None:
    if len(data) > MAX_FACE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Face image too large (max {MAX_FACE_BYTES // (1024 * 1024)} MB)",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty face image")
    ct = (content_type or "").lower()
    ok = ct in ("image/jpeg", "image/jpg", "image/png", "image/webp")
    if not ok:
        if data[:3] == b"\xff\xd8\xff":
            ok = True
        elif len(data) >= 4 and data[:4] == b"\x89PNG":
            ok = True
        elif len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            ok = True
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Face image must be JPEG, PNG, or WebP",
        )


def _validate_audio_bytes(data: bytes, content_type: Optional[str]) -> None:
    if len(data) > MAX_VOICE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio too large (max {MAX_VOICE_BYTES // (1024 * 1024)} MB)",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio file")
    ct = (content_type or "").lower()
    ok = ct in (
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
    )
    if not ok:
        if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
            ok = True
        elif data[:3] == b"ID3" or (len(data) >= 2 and data[:2] == b"\xff\xfb"):
            ok = True
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Audio must be WAV or MP3",
        )


@router.post("/face/verify", response_model=BiometricRecordResponse, status_code=201)
async def verify_face(
    request: Request,
    face_image: UploadFile = File(...),
    id_photo: Optional[UploadFile] = File(None),
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
    _validate_image_bytes(face_bytes, face_image.content_type)

    id_bytes: Optional[bytes] = None
    if id_photo is not None:
        id_bytes = await id_photo.read()
        if id_bytes:
            _validate_image_bytes(id_bytes, id_photo.content_type)

    device_info = {"user_agent": request.headers.get("user-agent")}
    ip_address = request.client.host if request.client else None

    record = await use_case.execute(
        user_id=user_id,
        face_image_bytes=face_bytes,
        id_photo_bytes=id_bytes if id_bytes else None,
        device_info=device_info,
        ip_address=ip_address,
    )

    await recalculate_trust_for_user_session(db, user_id)
    await db.commit()

    return _record_to_response(record)


@router.post("/voice/verify", response_model=BiometricRecordResponse, status_code=201)
async def verify_voice(
    request: Request,
    audio: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify voice biometric.

    Upload voice sample (WAV or MP3 recommended).
    """
    repo = SQLAlchemyBiometricRepository(db)
    use_case = VerifyVoiceUseCase(repo)

    audio_bytes = await audio.read()
    _validate_audio_bytes(audio_bytes, audio.content_type)

    device_info = {"user_agent": request.headers.get("user-agent")}
    ip_address = request.client.host if request.client else None

    record = await use_case.execute(
        user_id=user_id,
        audio_bytes=audio_bytes,
        device_info=device_info,
        ip_address=ip_address,
    )

    await recalculate_trust_for_user_session(db, user_id)
    await db.commit()

    return _record_to_response(record)


@router.get("/records", response_model=List[BiometricRecordResponse])
async def list_my_records(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List user's biometric records."""
    repo = SQLAlchemyBiometricRepository(db)
    records = await repo.list_by_user(user_id)

    return [_record_to_response(r) for r in records]


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

    return _record_to_response(record)


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

    owner_id = record.user_id
    await repo.delete(record_id)
    await recalculate_trust_for_user_session(db, owner_id)
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

    return [_record_to_response(r) for r in records]


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
    await recalculate_trust_for_user_session(db, updated.user_id)
    await db.commit()

    return _record_to_response(updated)


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
    await recalculate_trust_for_user_session(db, updated.user_id)
    await db.commit()

    logger.info(f"Biometric {record_id} rejected: {body.reason}")

    return _record_to_response(updated)


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
    await recalculate_trust_for_user_session(db, updated.user_id)
    await db.commit()

    return _record_to_response(updated)
