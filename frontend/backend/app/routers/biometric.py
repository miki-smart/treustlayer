import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUser, AdminUser, DB
from app.schemas.biometric import BiometricRecordOut, BiometricSubmitRequest, BiometricModelMetrics
from app.services import biometric_service
from app.models.user import UserRole


router = APIRouter(prefix="/biometric", tags=["Biometric"])


def _record_to_out(record, user_name: str) -> BiometricRecordOut:
    return BiometricRecordOut(
        id=record.id,
        userId=str(record.user_id),
        userName=user_name,
        type=record.type,
        status=record.status,
        livenessScore=record.liveness_score,
        spoofProbability=record.spoof_probability,
        timestamp=record.created_at.isoformat(),
        riskLevel=record.risk_level,
    )


@router.get("/records", response_model=list[BiometricRecordOut])
async def list_records(current_user: CurrentUser, db: DB):
    is_admin = current_user.role == UserRole.admin
    records = await biometric_service.get_records(db, current_user, is_admin)
    result = []
    for r in records:
        name = r.user.name if r.user else str(r.user_id)
        result.append(_record_to_out(r, name))
    return result


@router.get("/records/{record_id}", response_model=BiometricRecordOut)
async def get_record(record_id: uuid.UUID, current_user: CurrentUser, db: DB):
    record = await biometric_service.get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if current_user.role != UserRole.admin and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    name = record.user.name if record.user else str(record.user_id)
    return _record_to_out(record, name)


@router.post("/records", response_model=BiometricRecordOut, status_code=201)
async def submit_biometric(body: BiometricSubmitRequest, current_user: CurrentUser, db: DB):
    record = await biometric_service.submit_biometric(db, current_user, body.type)
    return _record_to_out(record, current_user.name)


@router.get("/metrics", response_model=BiometricModelMetrics)
async def get_metrics(current_user: CurrentUser):
    return BiometricModelMetrics(**biometric_service.BIOMETRIC_MODEL_METRICS)
