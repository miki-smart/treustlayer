"""
App registry router � OAuth2 client management and marketplace.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.api.dependencies import DBSession, CurrentUserId, require_admin
from app.modules.app_registry.infrastructure.persistence.app_repository_impl import SQLAlchemyAppRepository
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.app_registry.application.use_cases.register_app import RegisterAppUseCase
from app.modules.app_registry.application.use_cases.approve_app import ApproveAppUseCase
from app.modules.app_registry.application.use_cases.list_apps import ListAppsUseCase

router = APIRouter()


class AppResponse(BaseModel):
    id: str
    name: str
    client_id: str
    client_secret: Optional[str] = None
    api_key: Optional[str] = None
    owner_id: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str
    logo_url: Optional[str] = None
    category: str
    is_active: bool
    is_approved: bool
    is_public: bool
    created_at: str
    updated_at: str


class RegisterAppRequest(BaseModel):
    name: str
    allowed_scopes: List[str]
    redirect_uris: List[str]
    description: str = ""
    category: str = "general"
    logo_url: Optional[str] = None


@router.post("/", response_model=AppResponse, status_code=201)
async def register_app(
    payload: RegisterAppRequest,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Register new OAuth2 client application.
    
    Returns app details including client_secret and api_key (only shown once).
    """
    app_repo = SQLAlchemyAppRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    
    use_case = RegisterAppUseCase(app_repo, user_repo)
    
    app, client_secret, api_key = await use_case.execute(
        owner_id=current_user_id,
        name=payload.name,
        allowed_scopes=payload.allowed_scopes,
        redirect_uris=payload.redirect_uris,
        description=payload.description,
        category=payload.category,
        logo_url=payload.logo_url,
    )
    
    await session.commit()
    
    return AppResponse(
        id=app.id,
        name=app.name,
        client_id=app.client_id,
        client_secret=client_secret,
        api_key=api_key,
        owner_id=app.owner_id,
        allowed_scopes=app.allowed_scopes,
        redirect_uris=app.redirect_uris,
        description=app.description,
        logo_url=app.logo_url,
        category=app.category,
        is_active=app.is_active,
        is_approved=app.is_approved,
        is_public=app.is_public,
        created_at=app.created_at.isoformat(),
        updated_at=app.updated_at.isoformat(),
    )


@router.get("/", response_model=List[AppResponse])
async def list_apps(
    session: DBSession,
    _: None = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
):
    """
    List all apps (admin only).
    """
    app_repo = SQLAlchemyAppRepository(session)
    use_case = ListAppsUseCase(app_repo)
    
    apps = await use_case.list_all(skip, limit)
    
    return [
        AppResponse(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            owner_id=app.owner_id,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            logo_url=app.logo_url,
            category=app.category,
            is_active=app.is_active,
            is_approved=app.is_approved,
            is_public=app.is_public,
            created_at=app.created_at.isoformat(),
            updated_at=app.updated_at.isoformat(),
        )
        for app in apps
    ]


@router.get("/marketplace", response_model=List[AppResponse])
async def get_marketplace(session: DBSession, skip: int = 0, limit: int = 50):
    """
    Public app marketplace.
    
    Returns approved, public apps.
    """
    app_repo = SQLAlchemyAppRepository(session)
    use_case = ListAppsUseCase(app_repo)
    
    apps = await use_case.list_marketplace(skip, limit)
    
    return [
        AppResponse(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            owner_id=app.owner_id,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            logo_url=app.logo_url,
            category=app.category,
            is_active=app.is_active,
            is_approved=app.is_approved,
            is_public=app.is_public,
            created_at=app.created_at.isoformat(),
            updated_at=app.updated_at.isoformat(),
        )
        for app in apps
    ]


@router.get("/mine", response_model=List[AppResponse])
async def get_my_apps(
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Get apps owned by current user.
    """
    app_repo = SQLAlchemyAppRepository(session)
    use_case = ListAppsUseCase(app_repo)
    
    apps = await use_case.list_by_owner(current_user_id)
    
    return [
        AppResponse(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            owner_id=app.owner_id,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            logo_url=app.logo_url,
            category=app.category,
            is_active=app.is_active,
            is_approved=app.is_approved,
            is_public=app.is_public,
            created_at=app.created_at.isoformat(),
            updated_at=app.updated_at.isoformat(),
        )
        for app in apps
    ]


@router.post("/{app_id}/approve", response_model=AppResponse)
async def approve_app(
    app_id: str,
    session: DBSession,
    _: None = Depends(require_admin),
):
    """
    Approve app for use (admin only).
    """
    app_repo = SQLAlchemyAppRepository(session)
    use_case = ApproveAppUseCase(app_repo)
    
    await use_case.execute(app_id)
    
    app = await app_repo.get_by_id(app_id)
    
    await session.commit()
    
    return AppResponse(
        id=app.id,
        name=app.name,
        client_id=app.client_id,
        owner_id=app.owner_id,
        allowed_scopes=app.allowed_scopes,
        redirect_uris=app.redirect_uris,
        description=app.description,
        logo_url=app.logo_url,
        category=app.category,
        is_active=app.is_active,
        is_approved=app.is_approved,
        is_public=app.is_public,
        created_at=app.created_at.isoformat(),
        updated_at=app.updated_at.isoformat(),
    )


@router.post("/{app_id}/deactivate", response_model=AppResponse)
async def deactivate_app(
    app_id: str,
    session: DBSession,
    current_user_id: CurrentUserId,
):
    """
    Deactivate app.
    
    Owner or admin can deactivate.
    """
    app_repo = SQLAlchemyAppRepository(session)
    app = await app_repo.get_by_id(app_id)
    
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    if app.owner_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only app owner can deactivate")
    
    app.deactivate()
    await app_repo.update(app)
    
    await session.commit()
    
    return AppResponse(
        id=app.id,
        name=app.name,
        client_id=app.client_id,
        owner_id=app.owner_id,
        allowed_scopes=app.allowed_scopes,
        redirect_uris=app.redirect_uris,
        description=app.description,
        logo_url=app.logo_url,
        category=app.category,
        is_active=app.is_active,
        is_approved=app.is_approved,
        is_public=app.is_public,
        created_at=app.created_at.isoformat(),
        updated_at=app.updated_at.isoformat(),
    )
