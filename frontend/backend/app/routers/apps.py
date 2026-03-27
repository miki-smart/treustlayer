import uuid
import secrets
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query
from app.dependencies import CurrentUser, AdminUser, DB
from app.models.user import UserRole
from app.schemas.app_registry import (
    AppRegisterRequest, AppUpdateRequest, AppApproveRequest,
    RegisteredAppOut, AppCreatedResponse, UserAppOut,
    WebhookEndpointCreate, WebhookEndpointOut,
)
from app.services import app_service
from app.models.app_registry import AppStatus
from app.utils.security import hash_password

router = APIRouter(prefix="/apps", tags=["App Registry"])


# ── Spec-conformant response schema ──────────────────────────────────────────

class AppResponse(BaseModel):
    id: str
    name: str
    client_id: str
    client_secret: str | None = None
    api_key: str | None = None
    owner_id: str | None = None
    allowed_scopes: list[str]
    redirect_uris: list[str]
    description: str
    is_active: bool
    is_approved: bool


class AppRegistrationRequest(BaseModel):
    name: str
    allowed_scopes: list[str]
    redirect_uris: list[str]
    description: str = ""


class AppUpdateRequest2(BaseModel):
    name: str | None = None
    description: str | None = None
    allowed_scopes: list[str] | None = None
    redirect_uris: list[str] | None = None


def _app_response(app, plain_secret: str | None = None, plain_api_key: str | None = None) -> AppResponse:
    return AppResponse(
        id=str(app.id),
        name=app.name,
        client_id=app.client_id,
        client_secret=plain_secret,
        api_key=plain_api_key,
        owner_id=str(app.owner_id) if app.owner_id else None,
        allowed_scopes=app.allowed_scopes or [],
        redirect_uris=app.redirect_uris or [],
        description=app.description or "",
        is_active=app.status != AppStatus.suspended,
        is_approved=app.status == AppStatus.approved,
    )


def _app_to_out(app) -> RegisteredAppOut:
    return RegisteredAppOut(
        id=app.id,
        clientId=app.client_id,
        name=app.name,
        description=app.description,
        logoUrl=app.logo_url,
        websiteUrl=app.website_url,
        category=app.category,
        status=app.status,
        ownerId=str(app.owner_id),
        ownerName=app.owner.name if app.owner else "",
        allowedScopes=app.allowed_scopes,
        redirectUris=app.redirect_uris,
        isPublic=app.is_public,
        createdAt=app.created_at.isoformat() if app.created_at else "",
        approvedAt=app.approved_at.isoformat() if app.approved_at else None,
    )


# ── Public Marketplace ───────────────────────────────────────────────────────

@router.get("/marketplace", response_model=list[RegisteredAppOut], summary="Browse approved apps")
async def marketplace(db: DB):
    apps = await app_service.list_marketplace_apps(db)
    return [_app_to_out(a) for a in apps]


# ── App Registration ─────────────────────────────────────────────────────────

@router.post("", response_model=AppCreatedResponse, status_code=201, summary="Register a new app")
async def register_app(body: AppRegisterRequest, current_user: CurrentUser, db: DB):
    """
    Register an application to obtain a client_id and client_secret.
    The client_secret is returned **once** — store it securely.
    App is placed in 'pending' status until admin approves.
    """
    if not body.redirect_uris:
        raise HTTPException(status_code=422, detail="At least one redirect_uri is required")
    app, plain_secret = await app_service.register_app(db, current_user, body)
    out = _app_to_out(app)
    return AppCreatedResponse(**out.model_dump(), clientSecret=plain_secret)


@router.get("/mine", response_model=list[RegisteredAppOut], summary="My registered apps")
async def my_apps(current_user: CurrentUser, db: DB):
    apps = await app_service.list_my_apps(db, current_user)
    return [_app_to_out(a) for a in apps]


@router.get("/all", response_model=list[RegisteredAppOut], summary="All apps (admin only)")
async def all_apps(current_user: AdminUser, db: DB):
    apps = await app_service.list_all_apps(db)
    return [_app_to_out(a) for a in apps]


@router.get("/{app_id}", response_model=RegisteredAppOut, summary="Get app details")
async def get_app(app_id: uuid.UUID, db: DB):
    app = await app_service.get_app_by_id(db, app_id)
    return _app_to_out(app)


@router.patch("/{app_id}", response_model=RegisteredAppOut, summary="Update app details")
async def update_app(app_id: uuid.UUID, body: AppUpdateRequest, current_user: CurrentUser, db: DB):
    app = await app_service.update_app(db, app_id, body, current_user)
    return _app_to_out(app)


@router.post("/{app_id}/approve", response_model=RegisteredAppOut, summary="Approve/reject/suspend app (admin)")
async def approve_app(app_id: uuid.UUID, body: AppApproveRequest, current_user: AdminUser, db: DB):
    app = await app_service.approve_app(db, app_id, body, current_user)
    return _app_to_out(app)


# ── User Connected Apps ───────────────────────────────────────────────────────

@router.get("/user/connected", response_model=list[UserAppOut], summary="Apps I've connected to")
async def connected_apps(current_user: CurrentUser, db: DB):
    connections = await app_service.get_user_connected_apps(db, current_user)
    result = []
    for c in connections:
        result.append(UserAppOut(
            id=c.id,
            appId=str(c.app_id),
            appName=c.app.name if c.app else "",
            appLogoUrl=c.app.logo_url if c.app else None,
            appCategory=c.app.category if c.app else "other",
            connectedAt=c.connected_at.isoformat() if c.connected_at else "",
            lastUsed=c.last_used.isoformat() if c.last_used else None,
            isActive=c.is_active,
        ))
    return result


@router.post("/{app_id}/connect", response_model=UserAppOut, status_code=201, summary="Connect to an app")
async def connect_app(app_id: uuid.UUID, current_user: CurrentUser, db: DB):
    conn = await app_service.connect_app(db, current_user, app_id)
    return UserAppOut(
        id=conn.id,
        appId=str(conn.app_id),
        appName=conn.app.name if conn.app else "",
        appLogoUrl=conn.app.logo_url if conn.app else None,
        appCategory=conn.app.category if conn.app else "other",
        connectedAt=conn.connected_at.isoformat() if conn.connected_at else "",
        lastUsed=conn.last_used.isoformat() if conn.last_used else None,
        isActive=conn.is_active,
    )


@router.delete("/{app_id}/disconnect", status_code=204, summary="Disconnect from an app")
async def disconnect_app(app_id: uuid.UUID, current_user: CurrentUser, db: DB):
    await app_service.disconnect_app(db, current_user, app_id)


# ── Webhooks ──────────────────────────────────────────────────────────────────

@router.post("/{app_id}/webhooks", response_model=WebhookEndpointOut, status_code=201, summary="Add webhook endpoint")
async def add_webhook(app_id: uuid.UUID, body: WebhookEndpointCreate, current_user: CurrentUser, db: DB):
    """
    Register a webhook endpoint to receive events:
    - `kyc.approved` / `kyc.rejected` / `kyc.flagged`
    - `risk.alert`
    - `consent.revoked`
    - `identity.updated`
    """
    endpoint = await app_service.add_webhook(db, app_id, body, current_user)
    return WebhookEndpointOut(
        id=endpoint.id,
        appId=str(endpoint.app_id),
        url=endpoint.url,
        events=endpoint.events,
        enabled=endpoint.enabled,
        createdAt=endpoint.created_at.isoformat() if endpoint.created_at else "",
    )


@router.get("/{app_id}/webhooks", response_model=list[WebhookEndpointOut], summary="List webhook endpoints")
async def list_webhooks(app_id: uuid.UUID, current_user: CurrentUser, db: DB):
    endpoints = await app_service.list_webhooks(db, app_id, current_user)
    return [
        WebhookEndpointOut(
            id=e.id,
            appId=str(e.app_id),
            url=e.url,
            events=e.events,
            enabled=e.enabled,
            createdAt=e.created_at.isoformat() if e.created_at else "",
        )
        for e in endpoints
    ]


# ── TrustLayer ID spec routes (canonical) ───────────────────────────────────

@router.post("/", response_model=AppResponse, status_code=201, tags=["App Registry"], summary="Register a new OAuth2 client application")
async def register_app_v2(body: AppRegistrationRequest, current_user: CurrentUser, db: DB):
    """Returns client_secret once — store it securely."""
    class _Req:
        pass
    req = AppRegisterRequest(
        name=body.name,
        description=body.description,
        redirect_uris=body.redirect_uris,
        allowed_scopes=body.allowed_scopes,
        logo_url=None, website_url=None, category="other", is_public=False,
    )
    app, plain_secret = await app_service.register_app(db, current_user, req)
    return _app_response(app, plain_secret=plain_secret)


@router.get("/", response_model=list[AppResponse], tags=["App Registry"], summary="[Admin] List all registered applications")
async def list_apps_v2(
    current_user: AdminUser, db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    apps = await app_service.list_all_apps(db)
    return [_app_response(a) for a in apps[skip:skip + limit]]


@router.post("/{app_id}/approve", response_model=AppResponse, tags=["App Registry"], summary="[Admin] Approve a registered application")
async def approve_app_v2(app_id: str, current_user: AdminUser, db: DB):
    from app.schemas.app_registry import AppApproveRequest as AAR
    body = AAR(action="approve", notes="Approved")
    app = await app_service.approve_app(db, uuid.UUID(app_id), body, current_user)
    return _app_response(app)


@router.get("/{app_id}", response_model=AppResponse, tags=["App Registry"], summary="Get a registered application")
async def get_app_v2(app_id: str, db: DB):
    app = await app_service.get_app_by_id(db, uuid.UUID(app_id))
    return _app_response(app)


@router.patch("/{app_id}", response_model=AppResponse, tags=["App Registry"], summary="Update app configuration")
async def update_app_v2(app_id: str, body: AppUpdateRequest2, current_user: CurrentUser, db: DB):
    from app.schemas.app_registry import AppUpdateRequest as AUR
    upd = AUR(
        name=body.name, description=body.description,
        allowed_scopes=body.allowed_scopes, redirect_uris=body.redirect_uris,
    )
    app = await app_service.update_app(db, uuid.UUID(app_id), upd, current_user)
    return _app_response(app)


@router.post("/{app_id}/deactivate", response_model=AppResponse, tags=["App Registry"], summary="[Admin] Deactivate an application")
async def deactivate_app_v2(app_id: str, current_user: AdminUser, db: DB):
    from app.schemas.app_registry import AppApproveRequest as AAR
    body = AAR(action="suspend", notes="Deactivated by admin")
    app = await app_service.approve_app(db, uuid.UUID(app_id), body, current_user)
    return _app_response(app)


@router.post("/{app_id}/rotate-api-key", response_model=AppResponse, tags=["App Registry"], summary="Rotate the app's API key — returns new key once")
async def rotate_api_key(app_id: str, current_user: CurrentUser, db: DB):
    app = await app_service.get_app_by_id(db, uuid.UUID(app_id))
    if str(app.owner_id) != str(current_user.id) and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your app")
    plain_key = secrets.token_urlsafe(32)
    app.api_key_hash = hash_password(plain_key)
    return _app_response(app, plain_api_key=plain_key)


@router.post("/{app_id}/rotate-secret", response_model=AppResponse, tags=["App Registry"], summary="Rotate the app's OAuth2 client secret — returns new secret once")
async def rotate_client_secret(app_id: str, current_user: CurrentUser, db: DB):
    import bcrypt
    app = await app_service.get_app_by_id(db, uuid.UUID(app_id))
    if str(app.owner_id) != str(current_user.id) and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your app")
    plain_secret = secrets.token_urlsafe(32)
    app.client_secret_hash = hash_password(plain_secret)
    return _app_response(app, plain_secret=plain_secret)
