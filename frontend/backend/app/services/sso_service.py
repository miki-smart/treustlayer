import uuid
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sso import SSOProvider, SSOSession, ConsentRecord, SSOProviderStatus, SSOSessionStatus, ConsentStatus
from app.models.user import User
from app.schemas.sso import SSOProviderCreate, SSOProviderUpdate, ConsentCreate
from app.utils.audit import write_audit_entry


# --- Providers ---

async def get_providers(db: AsyncSession) -> list[SSOProvider]:
    result = await db.execute(select(SSOProvider).order_by(SSOProvider.name))
    return list(result.scalars().all())


async def get_provider_by_id(db: AsyncSession, provider_id: uuid.UUID) -> SSOProvider:
    result = await db.execute(select(SSOProvider).where(SSOProvider.id == provider_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="SSO provider not found")
    return p


async def create_provider(db: AsyncSession, data: SSOProviderCreate, actor: User) -> SSOProvider:
    provider = SSOProvider(
        id=uuid.uuid4(),
        name=data.name,
        protocol=data.protocol,
        status=SSOProviderStatus.pending,
        connected_at=datetime.now(timezone.utc).date().isoformat(),
        region=data.region,
    )
    db.add(provider)
    await write_audit_entry(
        db,
        action="SSO Provider Created",
        actor_id=actor.id,
        actor_name=actor.name,
        target=data.name,
        details=f"Provider {data.name} ({data.protocol}) registered",
    )
    return provider


async def update_provider(db: AsyncSession, provider_id: uuid.UUID, data: SSOProviderUpdate, actor: User) -> SSOProvider:
    provider = await get_provider_by_id(db, provider_id)
    if data.status is not None:
        provider.status = data.status
        provider.last_sync = datetime.now(timezone.utc).isoformat()
    if data.users_count is not None:
        provider.users_count = data.users_count
    await write_audit_entry(
        db,
        action="SSO Provider Updated",
        actor_id=actor.id,
        actor_name=actor.name,
        target=provider.name,
        details=f"Provider {provider.name} updated",
    )
    return provider


# --- Sessions ---

async def get_sessions(db: AsyncSession, user: User, is_admin: bool) -> list[SSOSession]:
    query = (
        select(SSOSession)
        .options(selectinload(SSOSession.provider), selectinload(SSOSession.user))
        .order_by(SSOSession.login_at.desc())
    )
    if not is_admin:
        query = query.where(SSOSession.user_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def revoke_session(db: AsyncSession, session_id: uuid.UUID, actor: User) -> None:
    result = await db.execute(select(SSOSession).where(SSOSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SSOSessionStatus.revoked
    await write_audit_entry(
        db,
        action="SSO Session Revoked",
        actor_id=actor.id,
        actor_name=actor.name,
        target=str(session.provider_id),
        details=f"Session {session_id} revoked",
    )


# --- Consents ---

async def get_consents(db: AsyncSession, user: User, is_admin: bool) -> list[ConsentRecord]:
    query = (
        select(ConsentRecord)
        .options(selectinload(ConsentRecord.provider))
        .order_by(ConsentRecord.granted_at.desc())
    )
    if not is_admin:
        query = query.where(ConsentRecord.user_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_consent(db: AsyncSession, user: User, data: ConsentCreate) -> ConsentRecord:
    consent = ConsentRecord(
        id=uuid.uuid4(),
        user_id=user.id,
        app_name=data.app_name,
        provider_id=data.provider_id,
        scopes_granted=data.scopes_granted,
        granted_at=datetime.now(timezone.utc),
        status=ConsentStatus.active,
    )
    db.add(consent)
    await write_audit_entry(
        db,
        action="Consent Granted",
        actor_id=user.id,
        actor_name=user.name,
        target=data.app_name,
        details=f"Consent granted for {data.app_name}: {', '.join(data.scopes_granted)}",
    )
    return consent


async def revoke_consent(db: AsyncSession, consent_id: uuid.UUID, actor: User) -> None:
    result = await db.execute(select(ConsentRecord).where(ConsentRecord.id == consent_id))
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    consent.status = ConsentStatus.revoked
    await write_audit_entry(
        db,
        action="Consent Revoked",
        actor_id=actor.id,
        actor_name=actor.name,
        target=consent.app_name,
        details=f"Consent {consent_id} revoked for {consent.app_name}",
    )
