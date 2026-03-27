from typing import Optional

from pydantic import BaseModel, field_validator


class AuthorizeRequest(BaseModel):
    """POST /auth/authorize — submit credentials + OAuth2 params."""
    username: str
    password: str
    client_id: str
    redirect_uri: str
    scope: str
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = "S256"


class AuthorizeResponse(BaseModel):
    code: str
    state: Optional[str] = None
    redirect_uri: str


class TokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    # authorization_code grant
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    code_verifier: Optional[str] = None
    # refresh_token grant
    refresh_token: Optional[str] = None

    @field_validator("grant_type")
    @classmethod
    def validate_grant_type(cls, v: str) -> str:
        allowed = {"authorization_code", "refresh_token"}
        if v not in allowed:
            raise ValueError(f"grant_type must be one of: {allowed}")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    scope: str


class UserInfoResponse(BaseModel):
    sub: str
    username: str
    email: str
    full_name: Optional[str]
    email_verified: bool
    kyc_tier: str
    trust_score: int
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """POST /auth/login — direct frontend user login."""
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    username: str
    role: str


class LogoutRequest(BaseModel):
    """POST /auth/logout — revoke the refresh token."""
    refresh_token: str


class IntrospectRequest(BaseModel):
    token: str
    client_id: str
    client_secret: str


class IntrospectResponse(BaseModel):
    active: bool
    sub: Optional[str] = None
    username: Optional[str] = None
    scopes: Optional[list] = None
    client_id: Optional[str] = None
    kyc_tier: Optional[str] = None
    trust_score: Optional[int] = None
    risk_flag: Optional[bool] = None
    exp: Optional[int] = None
    iss: Optional[str] = None
