from typing import List, Optional

from pydantic import BaseModel, HttpUrl, field_validator


class AppRegistrationRequest(BaseModel):
    name: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str = ""

    @field_validator("allowed_scopes")
    @classmethod
    def validate_scopes(cls, v: List[str]) -> List[str]:
        allowed = {
            "openid", "profile.basic", "profile.email", "profile.phone",
            "kyc.read", "kyc.full", "consent.read", "offline_access",
        }
        invalid = [s for s in v if s not in allowed]
        if invalid:
            raise ValueError(f"Unknown scopes: {invalid}")
        return v

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one redirect URI is required")
        return v


class AppUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_scopes: Optional[List[str]] = None
    redirect_uris: Optional[List[str]] = None

    @field_validator("allowed_scopes")
    @classmethod
    def validate_scopes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        allowed = {
            "openid", "profile.basic", "profile.email", "profile.phone",
            "kyc.read", "kyc.full", "consent.read", "offline_access",
        }
        invalid = [s for s in v if s not in allowed]
        if invalid:
            raise ValueError(f"Unknown scopes: {invalid}")
        return v

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and not v:
            raise ValueError("redirect_uris cannot be an empty list")
        return v


class AppResponse(BaseModel):
    id: str
    name: str
    client_id: str
    client_secret: Optional[str] = None  # only on creation / secret rotation
    api_key: Optional[str] = None        # only on creation / key rotation
    owner_id: Optional[str] = None
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str
    is_active: bool
    is_approved: bool

    model_config = {"from_attributes": True}
