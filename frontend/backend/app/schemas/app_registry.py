import uuid
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from app.models.app_registry import AppStatus, AppCategory


class AppRegisterRequest(BaseModel):
    name: str
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    category: AppCategory = AppCategory.other
    allowed_scopes: list[str] = ["openid", "profile", "email"]
    redirect_uris: list[str]
    is_public: bool = True


class AppUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    category: AppCategory | None = None
    allowed_scopes: list[str] | None = None
    redirect_uris: list[str] | None = None
    is_public: bool | None = None


class AppApproveRequest(BaseModel):
    status: AppStatus   # approved | rejected | suspended
    notes: str | None = None


class RegisteredAppOut(BaseModel):
    id: uuid.UUID
    clientId: str
    name: str
    description: str | None = None
    logoUrl: str | None = None
    websiteUrl: str | None = None
    category: AppCategory
    status: AppStatus
    ownerId: str
    ownerName: str
    allowedScopes: list[str]
    redirectUris: list[str]
    isPublic: bool
    createdAt: str
    approvedAt: str | None = None

    model_config = {"from_attributes": True}


class AppCreatedResponse(RegisteredAppOut):
    """Returned once at registration — includes the plain-text client secret."""
    clientSecret: str


class UserAppOut(BaseModel):
    id: uuid.UUID
    appId: str
    appName: str
    appLogoUrl: str | None = None
    appCategory: AppCategory
    connectedAt: str
    lastUsed: str | None = None
    isActive: bool

    model_config = {"from_attributes": True}


class WebhookEndpointCreate(BaseModel):
    url: str
    events: list[str]


class WebhookEndpointOut(BaseModel):
    id: uuid.UUID
    appId: str
    url: str
    events: list[str]
    enabled: bool
    createdAt: str

    model_config = {"from_attributes": True}


class WebhookDeliveryOut(BaseModel):
    id: uuid.UUID
    eventType: str
    status: str
    attempts: int
    responseStatus: int | None = None
    createdAt: str

    model_config = {"from_attributes": True}
