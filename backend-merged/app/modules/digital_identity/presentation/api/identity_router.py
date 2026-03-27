"""
Digital Identity API router.

Endpoints:
- POST /create — Create digital identity
- GET /me — Get my digital identity
- GET /{identity_id} — Get digital identity
- POST /{identity_id}/attributes — Add attribute
- GET /{identity_id}/attributes — List attributes
- PATCH /{identity_id}/attributes/{key} — Update attribute
- DELETE /{identity_id}/attributes/{key} — Delete attribute
- POST /{identity_id}/credentials — Issue credential
- GET /{identity_id}/credentials — List credentials
- POST /{identity_id}/credentials/{id}/revoke — Revoke credential
- POST /{identity_id}/suspend — [Admin] Suspend identity
- POST /{identity_id}/activate — [Admin] Activate identity
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user_id, require_admin
from app.modules.digital_identity.application.use_cases.create_identity import CreateDigitalIdentityUseCase
from app.modules.digital_identity.application.use_cases.manage_attributes import (
    AddAttributeUseCase,
    ListAttributesUseCase,
    UpdateAttributeUseCase,
    DeleteAttributeUseCase,
)
from app.modules.digital_identity.application.use_cases.manage_credentials import (
    IssueCredentialUseCase,
    ListCredentialsUseCase,
    RevokeCredentialUseCase,
)
from app.modules.digital_identity.infrastructure.persistence.identity_repository_impl import SQLAlchemyDigitalIdentityRepository
from app.modules.digital_identity.application.dto.identity_dto import (
    CreateIdentityRequest,
    IdentityResponse,
    AddAttributeRequest,
    AttributeResponse,
    UpdateAttributeRequest,
    IssueCredentialRequest,
    CredentialResponse,
)
from app.core.exceptions import DomainError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=IdentityResponse, status_code=201)
async def create_identity(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create digital identity for current user."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    use_case = CreateDigitalIdentityUseCase(repo)
    
    try:
        identity = await use_case.execute(user_id)
        await db.commit()
        
        return IdentityResponse(
            id=identity.id,
            user_id=identity.user_id,
            unique_id=identity.unique_id,
            status=identity.status.value,
            created_at=identity.created_at,
            last_verified=identity.last_verified,
        )
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=IdentityResponse)
async def get_my_identity(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get my digital identity."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    identity = await repo.get_by_user_id(user_id)
    
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    return IdentityResponse(
        id=identity.id,
        user_id=identity.user_id,
        unique_id=identity.unique_id,
        status=identity.status.value,
        created_at=identity.created_at,
        last_verified=identity.last_verified,
    )


@router.get("/{identity_id}", response_model=IdentityResponse)
async def get_identity(
    identity_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get digital identity by ID."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    identity = await repo.get_by_id(identity_id)
    
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    return IdentityResponse(
        id=identity.id,
        user_id=identity.user_id,
        unique_id=identity.unique_id,
        status=identity.status.value,
        created_at=identity.created_at,
        last_verified=identity.last_verified,
    )


@router.post("/{identity_id}/attributes", response_model=AttributeResponse, status_code=201)
async def add_attribute(
    identity_id: str,
    body: AddAttributeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add attribute to identity."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    
    identity = await repo.get_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    if identity.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    use_case = AddAttributeUseCase(repo)
    
    try:
        attr = await use_case.execute(
            identity_id=identity_id,
            key=body.key,
            value=body.value,
            is_shared=body.is_shared,
        )
        await db.commit()
        
        return AttributeResponse(
            id=attr.id,
            identity_id=attr.identity_id,
            key=attr.key,
            value=attr.value,
            is_shared=attr.is_shared,
            created_at=attr.created_at,
        )
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{identity_id}/attributes", response_model=List[AttributeResponse])
async def list_attributes(
    identity_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List identity attributes."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    
    identity = await repo.get_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    if identity.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    use_case = ListAttributesUseCase(repo)
    attrs = await use_case.execute(identity_id)
    
    return [
        AttributeResponse(
            id=a.id,
            identity_id=a.identity_id,
            key=a.key,
            value=a.value,
            is_shared=a.is_shared,
            created_at=a.created_at,
        )
        for a in attrs
    ]


@router.patch("/{identity_id}/attributes/{key}", response_model=AttributeResponse)
async def update_attribute(
    identity_id: str,
    key: str,
    body: UpdateAttributeRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update attribute."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    
    identity = await repo.get_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    if identity.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    use_case = UpdateAttributeUseCase(repo)
    
    try:
        attr = await use_case.execute(
            identity_id=identity_id,
            key=key,
            value=body.value,
            is_shared=body.is_shared,
        )
        await db.commit()
        
        return AttributeResponse(
            id=attr.id,
            identity_id=attr.identity_id,
            key=attr.key,
            value=attr.value,
            is_shared=attr.is_shared,
            created_at=attr.created_at,
        )
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{identity_id}/attributes/{key}", status_code=204)
async def delete_attribute(
    identity_id: str,
    key: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete attribute."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    
    identity = await repo.get_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    if identity.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    use_case = DeleteAttributeUseCase(repo)
    
    try:
        await use_case.execute(identity_id, key)
        await db.commit()
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{identity_id}/credentials", response_model=CredentialResponse, status_code=201, dependencies=[Depends(require_admin)])
async def issue_credential(
    identity_id: str,
    body: IssueCredentialRequest,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Issue verifiable credential."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    use_case = IssueCredentialUseCase(repo)
    
    try:
        cred = await use_case.execute(
            identity_id=identity_id,
            credential_type=body.type,
            credential_data=body.credential_data,
            expires_in_days=body.expires_in_days,
        )
        await db.commit()
        
        return CredentialResponse(
            id=cred.id,
            identity_id=cred.identity_id,
            type=cred.type,
            issuer=cred.issuer,
            credential_data=cred.credential_data,
            expires_at=cred.expires_at,
            status=cred.status,
            issued_at=cred.issued_at,
        )
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{identity_id}/credentials", response_model=List[CredentialResponse])
async def list_credentials(
    identity_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List identity credentials."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    
    identity = await repo.get_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    if identity.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    use_case = ListCredentialsUseCase(repo)
    creds = await use_case.execute(identity_id)
    
    return [
        CredentialResponse(
            id=c.id,
            identity_id=c.identity_id,
            type=c.type,
            issuer=c.issuer,
            credential_data=c.credential_data,
            expires_at=c.expires_at,
            status=c.status,
            issued_at=c.issued_at,
        )
        for c in creds
    ]


@router.post("/{identity_id}/credentials/{credential_id}/revoke", response_model=CredentialResponse, dependencies=[Depends(require_admin)])
async def revoke_credential(
    identity_id: str,
    credential_id: str,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Revoke credential."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    use_case = RevokeCredentialUseCase(repo)
    
    try:
        cred = await use_case.execute(credential_id)
        await db.commit()
        
        return CredentialResponse(
            id=cred.id,
            identity_id=cred.identity_id,
            type=cred.type,
            issuer=cred.issuer,
            credential_data=cred.credential_data,
            expires_at=cred.expires_at,
            status=cred.status,
            issued_at=cred.issued_at,
        )
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{identity_id}/suspend", response_model=IdentityResponse, dependencies=[Depends(require_admin)])
async def suspend_identity(
    identity_id: str,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Suspend digital identity."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    identity = await repo.get_by_id(identity_id)
    
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    identity.suspend()
    updated = await repo.update(identity)
    await db.commit()
    
    return IdentityResponse(
        id=updated.id,
        user_id=updated.user_id,
        unique_id=updated.unique_id,
        status=updated.status.value,
        created_at=updated.created_at,
        last_verified=updated.last_verified,
    )


@router.post("/{identity_id}/activate", response_model=IdentityResponse, dependencies=[Depends(require_admin)])
async def activate_identity(
    identity_id: str,
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Activate digital identity."""
    repo = SQLAlchemyDigitalIdentityRepository(db)
    identity = await repo.get_by_id(identity_id)
    
    if not identity:
        raise HTTPException(status_code=404, detail="Digital identity not found")
    
    identity.activate()
    updated = await repo.update(identity)
    await db.commit()
    
    return IdentityResponse(
        id=updated.id,
        user_id=updated.user_id,
        unique_id=updated.unique_id,
        status=updated.status.value,
        created_at=updated.created_at,
        last_verified=updated.last_verified,
    )
