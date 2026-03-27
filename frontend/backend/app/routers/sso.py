import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUser, AdminUser, DB
from app.schemas.sso import (
    SSOProviderOut, SSOProviderCreate, SSOProviderUpdate,
    SSOSessionOut, ConsentRecordOut, ConsentCreate,
)
from app.services import sso_service
from app.models.user import UserRole


router = APIRouter(prefix="/sso", tags=["SSO"])


# --- Providers ---

@router.get("/providers", response_model=list[SSOProviderOut])
async def list_providers(current_user: CurrentUser, db: DB):
    providers = await sso_service.get_providers(db)
    return [
        SSOProviderOut(
            id=p.id,
            name=p.name,
            protocol=p.protocol,
            status=p.status,
            connectedAt=p.connected_at,
            lastSync=p.last_sync,
            usersCount=p.users_count,
            region=p.region,
        )
        for p in providers
    ]


@router.post("/providers", response_model=SSOProviderOut, status_code=201)
async def create_provider(body: SSOProviderCreate, current_user: AdminUser, db: DB):
    provider = await sso_service.create_provider(db, body, current_user)
    return SSOProviderOut(
        id=provider.id,
        name=provider.name,
        protocol=provider.protocol,
        status=provider.status,
        connectedAt=provider.connected_at,
        lastSync=provider.last_sync,
        usersCount=provider.users_count,
        region=provider.region,
    )


@router.put("/providers/{provider_id}", response_model=SSOProviderOut)
async def update_provider(provider_id: uuid.UUID, body: SSOProviderUpdate, current_user: AdminUser, db: DB):
    provider = await sso_service.update_provider(db, provider_id, body, current_user)
    return SSOProviderOut(
        id=provider.id,
        name=provider.name,
        protocol=provider.protocol,
        status=provider.status,
        connectedAt=provider.connected_at,
        lastSync=provider.last_sync,
        usersCount=provider.users_count,
        region=provider.region,
    )


# --- Sessions ---

@router.get("/sessions", response_model=list[SSOSessionOut])
async def list_sessions(current_user: CurrentUser, db: DB):
    is_admin = current_user.role == UserRole.admin
    sessions = await sso_service.get_sessions(db, current_user, is_admin)
    return [
        SSOSessionOut(
            id=s.id,
            userId=str(s.user_id),
            userName=s.user.name if s.user else str(s.user_id),
            provider=s.provider.name if s.provider else str(s.provider_id),
            ipAddress=s.ip_address,
            device=s.device,
            loginAt=s.login_at.isoformat(),
            expiresAt=s.expires_at.isoformat(),
            status=s.status,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def revoke_session(session_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await sso_service.revoke_session(db, session_id, current_user)


# --- Consents ---

@router.get("/consents", response_model=list[ConsentRecordOut])
async def list_consents(current_user: CurrentUser, db: DB):
    is_admin = current_user.role == UserRole.admin
    consents = await sso_service.get_consents(db, current_user, is_admin)
    return [
        ConsentRecordOut(
            id=c.id,
            appName=c.app_name,
            provider=c.provider.name if c.provider else str(c.provider_id),
            scopesGranted=c.scopes_granted,
            grantedAt=c.granted_at.isoformat(),
            status=c.status,
        )
        for c in consents
    ]


@router.post("/consents", response_model=ConsentRecordOut, status_code=201)
async def create_consent(body: ConsentCreate, current_user: CurrentUser, db: DB):
    consent = await sso_service.create_consent(db, current_user, body)
    provider = await sso_service.get_provider_by_id(db, consent.provider_id)
    return ConsentRecordOut(
        id=consent.id,
        appName=consent.app_name,
        provider=provider.name,
        scopesGranted=consent.scopes_granted,
        grantedAt=consent.granted_at.isoformat(),
        status=consent.status,
    )


@router.delete("/consents/{consent_id}", status_code=204)
async def revoke_consent(consent_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await sso_service.revoke_consent(db, consent_id, current_user)
