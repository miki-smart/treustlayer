from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RegisterAppDTO:
    name: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str = ""
    owner_id: Optional[str] = field(default=None)


@dataclass
class AppResponseDTO:
    id: str
    name: str
    client_id: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str
    is_active: bool
    is_approved: bool
    owner_id: Optional[str] = field(default=None)
    # Returned ONLY at creation time; None afterwards.
    client_secret: Optional[str] = field(default=None)
    # Returned ONLY at creation time; None afterwards.
    api_key: Optional[str] = field(default=None)
