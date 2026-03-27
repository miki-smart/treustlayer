import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.identity import IdentityStatus


class IdentityAttributeSchema(BaseModel):
    key: str
    value: str
    shared: bool = False


class IdentityCredentialSchema(BaseModel):
    type: str
    issuer: str
    expiresAt: str
    status: str = "active"


class DigitalIdentityOut(BaseModel):
    id: uuid.UUID
    userId: str
    holderName: str
    uniqueId: str
    status: IdentityStatus
    createdAt: str
    lastVerified: str
    attributes: list[IdentityAttributeSchema]
    credentials: list[IdentityCredentialSchema]

    model_config = {"from_attributes": True}


class DigitalIdentityCreate(BaseModel):
    attributes: list[IdentityAttributeSchema] = []
    credentials: list[IdentityCredentialSchema] = []


class DigitalIdentityUpdate(BaseModel):
    attributes: list[IdentityAttributeSchema] | None = None
    credentials: list[IdentityCredentialSchema] | None = None


class IdentityStatusUpdate(BaseModel):
    status: IdentityStatus
