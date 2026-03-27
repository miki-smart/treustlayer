from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ConsentGrantRequest(BaseModel):
    user_id: str
    client_id: str
    scopes: List[str]


class ConsentRevokeRequest(BaseModel):
    user_id: str
    client_id: str


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    scopes: List[str]
    is_active: bool
    granted_at: datetime
    revoked_at: Optional[datetime] = None
