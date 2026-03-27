from fastapi import APIRouter, Query
from sqlalchemy import select
from app.dependencies import AdminUser, DB
from app.schemas.dashboard import AuditEntryOut
from app.models.audit import AuditEntry


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", response_model=list[AuditEntryOut])
async def list_audit_log(
    current_user: AdminUser,
    db: DB,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
):
    result = await db.execute(
        select(AuditEntry)
        .order_by(AuditEntry.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    entries = result.scalars().all()
    return [
        AuditEntryOut(
            id=str(e.id),
            action=e.action,
            actor=e.actor_name,
            target=e.target,
            timestamp=e.timestamp.isoformat(),
            details=e.details,
        )
        for e in entries
    ]
