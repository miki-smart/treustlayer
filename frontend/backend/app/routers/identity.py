import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import CurrentUser, DB
from app.schemas.identity import (
    DigitalIdentityOut, DigitalIdentityCreate, DigitalIdentityUpdate,
    IdentityStatusUpdate, IdentityAttributeSchema, IdentityCredentialSchema,
)
from app.services import identity_service
from app.models.user import UserRole


router = APIRouter(prefix="/identity", tags=["Digital Identity"])


def _identity_to_out(identity) -> DigitalIdentityOut:
    return DigitalIdentityOut(
        id=identity.id,
        userId=str(identity.user_id),
        holderName=identity.user.name if identity.user else str(identity.user_id),
        uniqueId=identity.unique_id,
        status=identity.status,
        createdAt=identity.created_at.isoformat(),
        lastVerified=identity.last_verified.isoformat(),
        attributes=[
            IdentityAttributeSchema(key=a.key, value=a.value, shared=a.shared)
            for a in identity.attributes
        ],
        credentials=[
            IdentityCredentialSchema(type=c.type, issuer=c.issuer, expiresAt=c.expires_at, status=c.status)
            for c in identity.credentials
        ],
    )


@router.get("/", response_model=list[DigitalIdentityOut])
async def list_identities(current_user: CurrentUser, db: DB):
    is_admin = current_user.role == UserRole.admin
    identities = await identity_service.get_identities(db, current_user, is_admin)
    return [_identity_to_out(i) for i in identities]


@router.get("/{identity_id}", response_model=DigitalIdentityOut)
async def get_identity(identity_id: uuid.UUID, current_user: CurrentUser, db: DB):
    identity = await identity_service.get_identity_by_id(db, identity_id)
    if current_user.role != UserRole.admin and identity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _identity_to_out(identity)


@router.post("/", response_model=DigitalIdentityOut, status_code=201)
async def create_identity(body: DigitalIdentityCreate, current_user: CurrentUser, db: DB):
    identity = await identity_service.create_identity(db, current_user, body)
    return _identity_to_out(identity)


@router.put("/{identity_id}", response_model=DigitalIdentityOut)
async def update_identity(identity_id: uuid.UUID, body: DigitalIdentityUpdate, current_user: CurrentUser, db: DB):
    identity = await identity_service.get_identity_by_id(db, identity_id)
    if current_user.role != UserRole.admin and identity.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    identity = await identity_service.update_identity(db, identity_id, body, current_user)
    return _identity_to_out(identity)


@router.patch("/{identity_id}/status", response_model=DigitalIdentityOut)
async def update_identity_status(identity_id: uuid.UUID, body: IdentityStatusUpdate, current_user: CurrentUser, db: DB):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    identity = await identity_service.update_identity_status(db, identity_id, body.status, current_user)
    return _identity_to_out(identity)
