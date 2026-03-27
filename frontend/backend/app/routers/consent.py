"""
Consent management — /api/v1/consent/*
"""
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, DB
from app.models.consent import ConsentGrant
from app.models.user import User

router = APIRouter(prefix="/consent", tags=["Consent"])


class ConsentGrantRequest(BaseModel):
    user_id: str
    client_id: str
    scopes: list[str]


class ConsentRevokeRequest(BaseModel):
    user_id: str
    client_id: str


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    scopes: list[str]
    is_active: bool
    granted_at: str
    revoked_at: str | None = None


def _out(c: ConsentGrant) -> ConsentResponse:
    return ConsentResponse(
        id=str(c.id),
        user_id=str(c.user_id),
        client_id=c.client_id,
        scopes=c.scopes,
        is_active=c.is_active,
        granted_at=c.granted_at.isoformat() if c.granted_at else "",
        revoked_at=c.revoked_at.isoformat() if c.revoked_at else None,
    )


@router.post("/grant", response_model=ConsentResponse, status_code=201, summary="Grant consent for a client to access specific scopes")
async def grant_consent(body: ConsentGrantRequest, db: DB):
    uid = uuid.UUID(body.user_id)
    # Update existing or create new
    existing = (await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.user_id == uid,
            ConsentGrant.client_id == body.client_id,
        )
    )).scalar_one_or_none()
    if existing:
        existing.scopes = body.scopes
        existing.is_active = True
        existing.revoked_at = None
        return _out(existing)
    grant = ConsentGrant(
        id=uuid.uuid4(),
        user_id=uid,
        client_id=body.client_id,
        scopes=body.scopes,
        is_active=True,
        granted_at=datetime.now(timezone.utc),
    )
    db.add(grant)
    await db.flush()
    return _out(grant)


@router.post("/revoke", status_code=204, summary="Revoke consent for a client")
async def revoke_consent(body: ConsentRevokeRequest, db: DB):
    uid = uuid.UUID(body.user_id)
    existing = (await db.execute(
        select(ConsentGrant).where(
            ConsentGrant.user_id == uid,
            ConsentGrant.client_id == body.client_id,
            ConsentGrant.is_active == True,
        )
    )).scalar_one_or_none()
    if existing:
        existing.is_active = False
        existing.revoked_at = datetime.now(timezone.utc)


@router.get("/user/{user_id}", response_model=list[ConsentResponse], summary="List all active consents for a user")
async def list_consents(user_id: str, db: DB):
    uid = uuid.UUID(user_id)
    result = await db.execute(
        select(ConsentGrant)
        .where(ConsentGrant.user_id == uid, ConsentGrant.is_active == True)
        .order_by(ConsentGrant.granted_at.desc())
    )
    return [_out(c) for c in result.scalars().all()]
