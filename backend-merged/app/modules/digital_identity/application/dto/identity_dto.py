"""
Digital Identity DTOs for API layer.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class CreateIdentityRequest(BaseModel):
    pass


class IdentityResponse(BaseModel):
    id: str
    user_id: str
    unique_id: str
    status: str
    created_at: datetime
    last_verified: datetime


class AddAttributeRequest(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1)
    is_shared: bool = False


class AttributeResponse(BaseModel):
    id: str
    identity_id: str
    key: str
    value: str
    is_shared: bool
    created_at: datetime


class UpdateAttributeRequest(BaseModel):
    value: Optional[str] = None
    is_shared: Optional[bool] = None


class IssueCredentialRequest(BaseModel):
    type: str = Field(..., min_length=1, max_length=255)
    credential_data: dict
    expires_in_days: int = Field(default=365, ge=1, le=3650)


class CredentialResponse(BaseModel):
    id: str
    identity_id: str
    type: str
    issuer: str
    credential_data: dict
    expires_at: datetime
    status: str
    issued_at: datetime
