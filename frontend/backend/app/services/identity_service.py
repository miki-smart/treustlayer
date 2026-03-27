import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import DigitalIdentity, IdentityAttribute, IdentityCredential, IdentityStatus
from app.models.user import User
from app.schemas.identity import DigitalIdentityCreate, DigitalIdentityUpdate, IdentityAttributeSchema, IdentityCredentialSchema
from app.utils.audit import write_audit_entry


def _generate_did(user: User) -> str:
    short = str(user.id).replace("-", "")[:8]
    return f"DID:FIN:ETH:0x{short}...{short[-4:]}"


async def get_identities(db: AsyncSession, user: User, is_admin: bool) -> list[DigitalIdentity]:
    query = (
        select(DigitalIdentity)
        .options(selectinload(DigitalIdentity.attributes), selectinload(DigitalIdentity.credentials))
    )
    if not is_admin:
        query = query.where(DigitalIdentity.user_id == user.id)
    result = await db.execute(query.order_by(DigitalIdentity.created_at.desc()))
    return list(result.scalars().all())


async def get_identity_by_id(db: AsyncSession, identity_id: uuid.UUID) -> DigitalIdentity:
    result = await db.execute(
        select(DigitalIdentity)
        .options(selectinload(DigitalIdentity.attributes), selectinload(DigitalIdentity.credentials))
        .where(DigitalIdentity.id == identity_id)
    )
    identity = result.scalar_one_or_none()
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    return identity


async def create_identity(db: AsyncSession, user: User, data: DigitalIdentityCreate) -> DigitalIdentity:
    identity = DigitalIdentity(
        id=uuid.uuid4(),
        user_id=user.id,
        unique_id=_generate_did(user),
        status=IdentityStatus.active,
        created_at=datetime.now(timezone.utc),
        last_verified=datetime.now(timezone.utc),
    )
    db.add(identity)
    await db.flush()

    for attr in data.attributes:
        db.add(IdentityAttribute(
            id=uuid.uuid4(),
            identity_id=identity.id,
            key=attr.key,
            value=attr.value,
            shared=attr.shared,
        ))

    for cred in data.credentials:
        db.add(IdentityCredential(
            id=uuid.uuid4(),
            identity_id=identity.id,
            type=cred.type,
            issuer=cred.issuer,
            expires_at=cred.expiresAt,
            status=cred.status,
        ))

    await write_audit_entry(
        db,
        action="Identity Created",
        actor_id=user.id,
        actor_name=user.name,
        target=user.name,
        details=f"Digital identity {identity.unique_id} created",
    )
    return identity


async def update_identity(db: AsyncSession, identity_id: uuid.UUID, data: DigitalIdentityUpdate, actor: User) -> DigitalIdentity:
    identity = await get_identity_by_id(db, identity_id)

    if data.attributes is not None:
        # Replace all attributes
        for attr in list(identity.attributes):
            await db.delete(attr)
        await db.flush()
        for attr in data.attributes:
            db.add(IdentityAttribute(
                id=uuid.uuid4(),
                identity_id=identity.id,
                key=attr.key,
                value=attr.value,
                shared=attr.shared,
            ))

    if data.credentials is not None:
        for cred in list(identity.credentials):
            await db.delete(cred)
        await db.flush()
        for cred in data.credentials:
            db.add(IdentityCredential(
                id=uuid.uuid4(),
                identity_id=identity.id,
                type=cred.type,
                issuer=cred.issuer,
                expires_at=cred.expiresAt,
                status=cred.status,
            ))

    identity.last_verified = datetime.now(timezone.utc)
    await write_audit_entry(
        db,
        action="Identity Updated",
        actor_id=actor.id,
        actor_name=actor.name,
        target=str(identity.user_id),
        details=f"Identity {identity_id} updated",
    )
    return identity


async def update_identity_status(db: AsyncSession, identity_id: uuid.UUID, new_status: IdentityStatus, actor: User) -> DigitalIdentity:
    identity = await get_identity_by_id(db, identity_id)
    old_status = identity.status
    identity.status = new_status
    await write_audit_entry(
        db,
        action=f"Identity {new_status.capitalize()}",
        actor_id=actor.id,
        actor_name=actor.name,
        target=str(identity.user_id),
        details=f"Identity {identity_id} changed from {old_status} to {new_status}",
    )
    return identity
