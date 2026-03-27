"""
Consent router � consent management.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import DBSession, CurrentUserId
from app.modules.consent.infrastructure.persistence.consent_repository_impl import SQLAlchemyConsentRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.consent.application.use_cases.grant_consent import GrantConsentUseCase
from app.modules.consent.application.use_cases.revoke_consent import RevokeConsentUseCase
from app.modules.consent.application.use_cases.list_user_consents import ListUserConsentsUseCase

router = APIRouter()


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    scopes: List[str]
    is_active: bool
    granted_at: str
    revoked_at: Optional[str] = None


class GrantConsentRequest(BaseModel):
    client_id: str
    scopes: List[str]


@router.post("/grant", status_code=201, response_model=ConsentResponse)
async def grant_consent(
    payload: GrantConsentRequest,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Grant consent for OAuth2 client.
    
    If consent already exists, updates scopes.
    """
    consent_repo = SQLAlchemyConsentRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    
    use_case = GrantConsentUseCase(consent_repo, user_repo)
    consent = await use_case.execute(current_user_id, payload.client_id, payload.scopes)
    
    await session.commit()
    
    return ConsentResponse(
        id=consent.id,
        user_id=consent.user_id,
        client_id=consent.client_id,
        scopes=consent.scopes,
        is_active=consent.is_active,
        granted_at=consent.granted_at.isoformat(),
        revoked_at=consent.revoked_at.isoformat() if consent.revoked_at else None,
    )


class RevokeConsentRequest(BaseModel):
    client_id: str


@router.post("/revoke", status_code=204)
async def revoke_consent(
    payload: RevokeConsentRequest,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Revoke consent for OAuth2 client.
    """
    consent_repo = SQLAlchemyConsentRepository(session)
    
    use_case = RevokeConsentUseCase(consent_repo)
    await use_case.execute(current_user_id, payload.client_id)
    
    await session.commit()
    
    return None


@router.get("/me", response_model=List[ConsentResponse])
async def list_my_consents(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    List current user's consents.
    """
    consent_repo = SQLAlchemyConsentRepository(session)
    
    use_case = ListUserConsentsUseCase(consent_repo)
    consents = await use_case.execute(current_user_id)
    
    return [
        ConsentResponse(
            id=c.id,
            user_id=c.user_id,
            client_id=c.client_id,
            scopes=c.scopes,
            is_active=c.is_active,
            granted_at=c.granted_at.isoformat(),
            revoked_at=c.revoked_at.isoformat() if c.revoked_at else None,
        )
        for c in consents
    ]


@router.get("/user/{user_id}", response_model=List[ConsentResponse])
async def list_user_consents(
    user_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    List consents for specific user.
    
    Users can only see their own consents unless admin.
    """
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot view other user's consents")
    
    consent_repo = SQLAlchemyConsentRepository(session)
    
    use_case = ListUserConsentsUseCase(consent_repo)
    consents = await use_case.execute(user_id)
    
    return [
        ConsentResponse(
            id=c.id,
            user_id=c.user_id,
            client_id=c.client_id,
            scopes=c.scopes,
            is_active=c.is_active,
            granted_at=c.granted_at.isoformat(),
            revoked_at=c.revoked_at.isoformat() if c.revoked_at else None,
        )
        for c in consents
    ]
