"""
App Registry service — registration, approval, marketplace, webhooks.
"""
import uuid
import secrets
import hmac
import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_registry import RegisteredApp, AppStatus, AuthorizationCode, UserApp
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.models.user import User
from app.schemas.app_registry import AppRegisterRequest, AppUpdateRequest, AppApproveRequest, WebhookEndpointCreate
from app.utils.audit import write_audit_entry
from app.utils.security import hash_password, verify_password


def _generate_client_id() -> str:
    return "app_" + secrets.token_urlsafe(16)


def _generate_client_secret() -> str:
    return secrets.token_urlsafe(32)


# ── App Registration ──────────────────────────────────────────────────────────

async def register_app(db: AsyncSession, owner: User, data: AppRegisterRequest) -> tuple[RegisteredApp, str]:
    """Returns (app, plain_client_secret) — secret is shown only once."""
    client_id = _generate_client_id()
    plain_secret = _generate_client_secret()
    app = RegisteredApp(
        id=uuid.uuid4(),
        client_id=client_id,
        client_secret_hash=hash_password(plain_secret),
        name=data.name,
        description=data.description,
        logo_url=data.logo_url,
        website_url=data.website_url,
        category=data.category,
        status=AppStatus.pending,
        owner_id=owner.id,
        allowed_scopes=data.allowed_scopes,
        redirect_uris=data.redirect_uris,
        is_public=data.is_public,
        created_at=datetime.now(timezone.utc),
    )
    db.add(app)
    await write_audit_entry(
        db, action="App Registered",
        actor_id=owner.id, actor_name=owner.name,
        target=data.name,
        details=f"App '{data.name}' registered by {owner.email}, awaiting approval",
    )
    return app, plain_secret


async def get_app_by_id(db: AsyncSession, app_id: uuid.UUID) -> RegisteredApp:
    result = await db.execute(
        select(RegisteredApp)
        .options(selectinload(RegisteredApp.owner))
        .where(RegisteredApp.id == app_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return app


async def get_app_by_client_id(db: AsyncSession, client_id: str) -> RegisteredApp | None:
    result = await db.execute(select(RegisteredApp).where(RegisteredApp.client_id == client_id))
    return result.scalar_one_or_none()


async def list_marketplace_apps(db: AsyncSession) -> list[RegisteredApp]:
    """Public marketplace — only approved, public apps."""
    result = await db.execute(
        select(RegisteredApp)
        .options(selectinload(RegisteredApp.owner))
        .where(RegisteredApp.status == AppStatus.approved, RegisteredApp.is_public == True)
        .order_by(RegisteredApp.name)
    )
    return list(result.scalars().all())


async def list_all_apps(db: AsyncSession) -> list[RegisteredApp]:
    """Admin: all apps regardless of status."""
    result = await db.execute(
        select(RegisteredApp)
        .options(selectinload(RegisteredApp.owner))
        .order_by(RegisteredApp.created_at.desc())
    )
    return list(result.scalars().all())


async def list_my_apps(db: AsyncSession, owner: User) -> list[RegisteredApp]:
    result = await db.execute(
        select(RegisteredApp)
        .options(selectinload(RegisteredApp.owner))
        .where(RegisteredApp.owner_id == owner.id)
        .order_by(RegisteredApp.created_at.desc())
    )
    return list(result.scalars().all())


async def update_app(db: AsyncSession, app_id: uuid.UUID, data: AppUpdateRequest, actor: User) -> RegisteredApp:
    app = await get_app_by_id(db, app_id)
    if actor.role != "admin" and app.owner_id != actor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(app, field, value)
    return app


async def approve_app(db: AsyncSession, app_id: uuid.UUID, data: AppApproveRequest, admin: User) -> RegisteredApp:
    app = await get_app_by_id(db, app_id)
    app.status = data.status
    if data.status == AppStatus.approved:
        app.approved_at = datetime.now(timezone.utc)
        app.approved_by_id = admin.id
    await write_audit_entry(
        db, action=f"App {data.status.capitalize()}",
        actor_id=admin.id, actor_name=admin.name,
        target=app.name,
        details=f"App '{app.name}' set to {data.status}. Notes: {data.notes or '—'}",
    )
    return app


# ── User ↔ App Connections ────────────────────────────────────────────────────

async def get_user_connected_apps(db: AsyncSession, user: User) -> list[UserApp]:
    result = await db.execute(
        select(UserApp)
        .options(selectinload(UserApp.app))
        .where(UserApp.user_id == user.id, UserApp.is_active == True)
        .order_by(UserApp.connected_at.desc())
    )
    return list(result.scalars().all())


async def connect_app(db: AsyncSession, user: User, app_id: uuid.UUID) -> UserApp:
    app = await get_app_by_id(db, app_id)
    if app.status != AppStatus.approved:
        raise HTTPException(status_code=400, detail="App is not approved for use")
    # Check if already connected
    existing = await db.execute(
        select(UserApp).where(UserApp.user_id == user.id, UserApp.app_id == app_id)
    )
    conn = existing.scalar_one_or_none()
    if conn:
        conn.is_active = True
        conn.last_used = datetime.now(timezone.utc)
        return conn
    conn = UserApp(
        id=uuid.uuid4(),
        user_id=user.id,
        app_id=app_id,
        connected_at=datetime.now(timezone.utc),
    )
    db.add(conn)
    return conn


async def disconnect_app(db: AsyncSession, user: User, app_id: uuid.UUID) -> None:
    result = await db.execute(
        select(UserApp).where(UserApp.user_id == user.id, UserApp.app_id == app_id)
    )
    conn = result.scalar_one_or_none()
    if conn:
        conn.is_active = False


# ── Webhooks ──────────────────────────────────────────────────────────────────

async def add_webhook(db: AsyncSession, app_id: uuid.UUID, data: WebhookEndpointCreate, actor: User) -> WebhookEndpoint:
    app = await get_app_by_id(db, app_id)
    if actor.role != "admin" and app.owner_id != actor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    endpoint = WebhookEndpoint(
        id=uuid.uuid4(),
        app_id=app_id,
        url=data.url,
        events=data.events,
        secret=secrets.token_urlsafe(32),
        enabled=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(endpoint)
    return endpoint


async def list_webhooks(db: AsyncSession, app_id: uuid.UUID, actor: User) -> list[WebhookEndpoint]:
    app = await get_app_by_id(db, app_id)
    if actor.role != "admin" and app.owner_id != actor.id:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(WebhookEndpoint).where(WebhookEndpoint.app_id == app_id))
    return list(result.scalars().all())


async def dispatch_webhook_event(db: AsyncSession, user_id: uuid.UUID, event_type: str, payload: dict) -> None:
    """Find all webhook endpoints subscribed to event_type for apps connected to this user, create deliveries."""
    user_app_result = await db.execute(
        select(UserApp)
        .options(selectinload(UserApp.app).selectinload(RegisteredApp.webhook_endpoints))
        .where(UserApp.user_id == user_id, UserApp.is_active == True)
    )
    for ua in user_app_result.scalars().all():
        for endpoint in ua.app.webhook_endpoints:
            if endpoint.enabled and event_type in endpoint.events:
                delivery = WebhookDelivery(
                    id=uuid.uuid4(),
                    endpoint_id=endpoint.id,
                    event_type=event_type,
                    payload=payload,
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(delivery)
