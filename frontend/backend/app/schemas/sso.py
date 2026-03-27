import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.sso import SSOProtocol, SSOProviderStatus, SSOSessionStatus, ConsentStatus


class SSOProviderOut(BaseModel):
    id: uuid.UUID
    name: str
    protocol: SSOProtocol
    status: SSOProviderStatus
    connectedAt: str
    lastSync: str | None = None
    usersCount: int
    region: str

    model_config = {"from_attributes": True}


class SSOProviderCreate(BaseModel):
    name: str
    protocol: SSOProtocol
    region: str = ""


class SSOProviderUpdate(BaseModel):
    status: SSOProviderStatus | None = None
    users_count: int | None = None


class SSOSessionOut(BaseModel):
    id: uuid.UUID
    userId: str
    userName: str
    provider: str
    ipAddress: str
    device: str
    loginAt: str
    expiresAt: str
    status: SSOSessionStatus

    model_config = {"from_attributes": True}


class ConsentRecordOut(BaseModel):
    id: uuid.UUID
    appName: str
    provider: str
    scopesGranted: list[str]
    grantedAt: str
    status: ConsentStatus

    model_config = {"from_attributes": True}


class ConsentCreate(BaseModel):
    app_name: str
    provider_id: uuid.UUID
    scopes_granted: list[str]
