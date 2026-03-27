import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEntry


async def write_audit_entry(
    db: AsyncSession,
    *,
    action: str,
    actor_id: uuid.UUID | None = None,
    actor_name: str = "System",
    target: str = "",
    details: str = "",
) -> AuditEntry:
    entry = AuditEntry(
        id=uuid.uuid4(),
        action=action,
        actor_id=actor_id,
        actor_name=actor_name,
        target=target,
        timestamp=datetime.now(timezone.utc),
        details=details,
    )
    db.add(entry)
    await db.flush()
    return entry
