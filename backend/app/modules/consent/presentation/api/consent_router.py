from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.modules.consent.application.services.consent_service import ConsentService
from app.modules.consent.infrastructure.persistence.consent_repository_impl import SQLAlchemyConsentRepository
from app.modules.consent.presentation.schemas.consent_schemas import (
    ConsentGrantRequest,
    ConsentResponse,
    ConsentRevokeRequest,
)

router = APIRouter(prefix="/consent", tags=["Consent"])


def _svc(session: AsyncSession) -> ConsentService:
    return ConsentService(SQLAlchemyConsentRepository(session))


@router.post(
    "/grant",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant consent for a client to access specific scopes",
)
async def grant_consent(
    payload: ConsentGrantRequest,
    session: AsyncSession = Depends(get_async_session),
):
    svc = _svc(session)
    consent = await svc.grant_consent(
        user_id=payload.user_id,
        client_id=payload.client_id,
        scopes=payload.scopes,
    )
    await session.commit()
    return ConsentResponse(
        id=consent.id,
        user_id=consent.user_id,
        client_id=consent.client_id,
        scopes=consent.scopes,
        is_active=consent.is_active,
        granted_at=consent.granted_at,
        revoked_at=consent.revoked_at,
    )


@router.post(
    "/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke consent for a client",
)
async def revoke_consent(
    payload: ConsentRevokeRequest,
    session: AsyncSession = Depends(get_async_session),
):
    svc = _svc(session)
    await svc.revoke_consent(user_id=payload.user_id, client_id=payload.client_id)
    await session.commit()


@router.get(
    "/user/{user_id}",
    response_model=List[ConsentResponse],
    summary="List all active consents for a user",
)
async def list_consents(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    svc = _svc(session)
    consents = await svc.list_consents(user_id)
    return [
        ConsentResponse(
            id=c.id,
            user_id=c.user_id,
            client_id=c.client_id,
            scopes=c.scopes,
            is_active=c.is_active,
            granted_at=c.granted_at,
            revoked_at=c.revoked_at,
        )
        for c in consents
    ]
