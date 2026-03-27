from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_current_user_role, require_role
from app.core.database import get_async_session
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.app_registry.application.dto.app_dto import RegisterAppDTO
from app.modules.app_registry.application.use_cases.app_use_cases import (
    ApproveAppUseCase,
    DeactivateAppUseCase,
    ListOwnAppsUseCase,
    RegisterAppUseCase,
    RotateApiKeyUseCase,
    RotateClientSecretUseCase,
    UpdateAppUseCase,
)
from app.modules.app_registry.infrastructure.persistence.app_repository_impl import (
    SQLAlchemyAppRepository,
)
from app.modules.app_registry.presentation.schemas.app_schemas import (
    AppRegistrationRequest,
    AppResponse,
    AppUpdateRequest,
)
from app.modules.identity.domain.entities.user import UserRole

router = APIRouter(prefix="/apps", tags=["App Registry"])


def _repo(session: AsyncSession) -> SQLAlchemyAppRepository:
    return SQLAlchemyAppRepository(session)


@router.post(
    "/",
    response_model=AppResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new OAuth2 client application",
)
async def register_app(
    payload: AppRegistrationRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Requires authentication. The caller becomes the app owner."""
    use_case = RegisterAppUseCase(_repo(session))
    result = await use_case.execute(
        RegisterAppDTO(
            name=payload.name,
            allowed_scopes=payload.allowed_scopes,
            redirect_uris=payload.redirect_uris,
            description=payload.description,
            owner_id=current_user_id,
        )
    )
    await session.commit()
    return AppResponse(**result.__dict__)


@router.get(
    "/mine",
    response_model=List[AppResponse],
    summary="List apps owned by the current user",
)
async def list_my_apps(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
):
    results = await ListOwnAppsUseCase(_repo(session)).execute(
        owner_id=current_user_id, skip=skip, limit=limit
    )
    return [AppResponse(**r.__dict__) for r in results]


@router.get(
    "/",
    response_model=List[AppResponse],
    summary="[Admin] List all registered applications",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_apps(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    apps = await _repo(session).get_all(skip=skip, limit=limit)
    return [AppResponse(**a.__dict__) for a in apps]


@router.post(
    "/{app_id}/approve",
    response_model=AppResponse,
    summary="[Admin] Approve a registered application",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def approve_app(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await ApproveAppUseCase(_repo(session)).execute(app_id)
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{app_id}",
    response_model=AppResponse,
    summary="Get a registered application",
)
async def get_app(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    app = await _repo(session).get_by_id(app_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    return AppResponse(**app.__dict__)


@router.patch(
    "/{app_id}",
    response_model=AppResponse,
    summary="Update app configuration (owner or admin)",
)
async def update_app(
    app_id: str,
    payload: AppUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
    current_role: str = Depends(get_current_user_role),
):
    try:
        result = await UpdateAppUseCase(_repo(session)).execute(
            app_id,
            caller_id=current_user_id,
            caller_role=current_role,
            name=payload.name,
            description=payload.description,
            allowed_scopes=payload.allowed_scopes,
            redirect_uris=payload.redirect_uris,
        )
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/{app_id}/deactivate",
    response_model=AppResponse,
    summary="[Admin] Deactivate an application",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def deactivate_app(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await DeactivateAppUseCase(_repo(session)).execute(app_id)
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{app_id}/rotate-api-key",
    response_model=AppResponse,
    summary="Rotate the app's API key — returns new key once (owner or admin)",
)
async def rotate_api_key(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
    current_role: str = Depends(get_current_user_role),
):
    try:
        result = await RotateApiKeyUseCase(_repo(session)).execute(
            app_id, caller_id=current_user_id, caller_role=current_role
        )
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/{app_id}/rotate-secret",
    response_model=AppResponse,
    summary="Rotate the app's OAuth2 client secret — returns new secret once (owner or admin)",
)
async def rotate_client_secret(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
    current_role: str = Depends(get_current_user_role),
):
    try:
        result = await RotateClientSecretUseCase(_repo(session)).execute(
            app_id, caller_id=current_user_id, caller_role=current_role
        )
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

router = APIRouter(prefix="/apps", tags=["App Registry"])


def _repo(session: AsyncSession) -> SQLAlchemyAppRepository:
    return SQLAlchemyAppRepository(session)


@router.post(
    "/",
    response_model=AppResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new OAuth2 client application",
)
async def register_app(
    payload: AppRegistrationRequest,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = RegisterAppUseCase(_repo(session))
    result = await use_case.execute(
        RegisterAppDTO(
            name=payload.name,
            allowed_scopes=payload.allowed_scopes,
            redirect_uris=payload.redirect_uris,
            description=payload.description,
        )
    )
    await session.commit()
    return AppResponse(**result.__dict__)


@router.get(
    "/",
    response_model=List[AppResponse],
    summary="[Admin] List all registered applications",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_apps(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    apps = await _repo(session).get_all(skip=skip, limit=limit)
    return [
        AppResponse(
            id=a.id,
            name=a.name,
            client_id=a.client_id,
            allowed_scopes=a.allowed_scopes,
            redirect_uris=a.redirect_uris,
            description=a.description,
            is_active=a.is_active,
            is_approved=a.is_approved,
        )
        for a in apps
    ]


@router.post(
    "/{app_id}/approve",
    response_model=AppResponse,
    summary="[Admin] Approve a registered application",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def approve_app(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = ApproveAppUseCase(_repo(session))
    try:
        result = await use_case.execute(app_id)
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{app_id}",
    response_model=AppResponse,
    summary="Get a registered application",
)
async def get_app(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    repo = _repo(session)
    app = await repo.get_by_id(app_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    return AppResponse(
        id=app.id,
        name=app.name,
        client_id=app.client_id,
        allowed_scopes=app.allowed_scopes,
        redirect_uris=app.redirect_uris,
        description=app.description,
        is_active=app.is_active,
        is_approved=app.is_approved,
    )


@router.patch(
    "/{app_id}",
    response_model=AppResponse,
    summary="Update app configuration (name, description, scopes, redirect URIs)",
)
async def update_app(
    app_id: str,
    payload: AppUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await UpdateAppUseCase(_repo(session)).execute(
            app_id,
            name=payload.name,
            description=payload.description,
            allowed_scopes=payload.allowed_scopes,
            redirect_uris=payload.redirect_uris,
        )
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{app_id}/deactivate",
    response_model=AppResponse,
    summary="[Admin] Deactivate an application",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def deactivate_app(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await DeactivateAppUseCase(_repo(session)).execute(app_id)
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{app_id}/rotate-api-key",
    response_model=AppResponse,
    summary="Rotate the app's API key — returns new key once",
)
async def rotate_api_key(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await RotateApiKeyUseCase(_repo(session)).execute(app_id)
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{app_id}/rotate-secret",
    response_model=AppResponse,
    summary="Rotate the app's OAuth2 client secret — returns new secret once",
)
async def rotate_client_secret(
    app_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await RotateClientSecretUseCase(_repo(session)).execute(app_id)
        await session.commit()
        return AppResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
