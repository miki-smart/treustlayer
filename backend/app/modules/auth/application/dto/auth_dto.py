from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AuthorizeDTO:
    username: str
    password: str
    client_id: str
    redirect_uri: str
    scope: str  # space-separated
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = "S256"

    def scopes_list(self) -> List[str]:
        return [s for s in self.scope.split() if s]


@dataclass
class AuthorizeResultDTO:
    code: str
    state: Optional[str]
    redirect_uri: str


@dataclass
class TokenRequestDTO:
    grant_type: str  # "authorization_code" | "refresh_token"
    client_id: str
    client_secret: str
    # authorization_code fields
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    code_verifier: Optional[str] = None
    # refresh_token fields
    refresh_token: Optional[str] = None


@dataclass
class TokenResponseDTO:
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "Bearer"
    expires_in: int = 900  # seconds
    scope: str = ""


@dataclass
class UserInfoDTO:
    sub: str
    username: str
    email: str
    full_name: Optional[str]
    email_verified: bool
    kyc_tier: str
    trust_score: int


@dataclass
class IntrospectResponseDTO:
    active: bool
    sub: Optional[str] = None
    scopes: Optional[str] = None
    client_id: Optional[str] = None
    kyc_tier: Optional[str] = None
    trust_score: Optional[int] = None
    risk_flag: Optional[bool] = None
    exp: Optional[int] = None
    iss: Optional[str] = None
