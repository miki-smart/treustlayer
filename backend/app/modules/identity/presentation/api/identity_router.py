from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user_id,
    require_role,
)
from app.core.database import get_async_session
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from app.modules.identity.application.dto.user_dto import RegisterUserDTO, UpdateProfileDTO
from app.modules.identity.application.use_cases.email_verification import (
    SendEmailVerificationUseCase,
    VerifyEmailUseCase,
)
from app.modules.identity.application.use_cases.password_management import (
    ChangePasswordUseCase,
    ForgotPasswordUseCase,
    ResetPasswordUseCase,
)
from app.modules.identity.application.use_cases.register_user import RegisterUserUseCase
from app.modules.identity.application.use_cases.user_management import (
    AssignRoleUseCase,
    DeactivateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserProfileUseCase,
)
from app.modules.identity.domain.entities.user import UserRole
from app.modules.identity.infrastructure.persistence.user_repository_impl import (
    SQLAlchemyUserRepository,
)
from app.modules.identity.presentation.schemas.user_schemas import (
    UserRegistrationRequest,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter(prefix="/identity", tags=["Identity"])


def _repo(session: AsyncSession) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)


# ─── Registration ─────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    payload: UserRegistrationRequest,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = RegisterUserUseCase(_repo(session))
    try:
        result = await use_case.execute(
            RegisterUserDTO(
                email=payload.email,
                username=payload.username,
                password=payload.password,
                full_name=payload.full_name,
                phone_number=payload.phone_number,
            )
        )
        await session.commit()
        return UserResponse(**result.__dict__)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ─── Profile ──────────────────────────────────────────────────────────────────

@router.get(
    "/users/me",
    response_model=UserResponse,
    summary="Get current user's own profile",
)
async def get_my_profile(
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
):
    use_case = GetUserUseCase(_repo(session))
    try:
        result = await use_case.execute(current_user_id)
        return UserResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user profile",
)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
    _current_user_id: str = Depends(get_current_user_id),
):
    use_case = GetUserUseCase(_repo(session))
    try:
        result = await use_case.execute(user_id)
        return UserResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user profile",
)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    _current_user_id: str = Depends(get_current_user_id),
):
    use_case = UpdateUserProfileUseCase(_repo(session))
    try:
        result = await use_case.execute(
            UpdateProfileDTO(
                user_id=user_id,
                full_name=payload.full_name,
                phone_number=payload.phone_number,
            )
        )
        await session.commit()
        return UserResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ─── Password management ──────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password-reset email",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Always returns 202 — never reveals whether the email exists."""
    await ForgotPasswordUseCase(_repo(session)).execute(payload.email)
    await session.commit()
    return {"message": "If that email is registered you will receive a reset link."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using the emailed token",
)
async def reset_password(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        await ResetPasswordUseCase(_repo(session)).execute(payload.token, payload.new_password)
        await session.commit()
        return {"message": "Password updated successfully."}
    except (UnauthorizedError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/users/{user_id}/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change own password (authenticated)",
)
async def change_password(
    user_id: str,
    payload: ChangePasswordRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
):
    # Users may only change their own password
    if current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        await ChangePasswordUseCase(_repo(session)).execute(
            user_id, payload.current_password, payload.new_password
        )
        await session.commit()
        return {"message": "Password changed successfully."}
    except (UnauthorizedError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ─── Email verification ───────────────────────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    token: str


@router.post(
    "/send-verification-email",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send (or resend) an email-verification link to the current user",
)
async def send_verification_email(
    session: AsyncSession = Depends(get_async_session),
    current_user_id: str = Depends(get_current_user_id),
):
    await SendEmailVerificationUseCase(_repo(session)).execute(current_user_id)
    await session.commit()
    return {"message": "Verification email sent."}


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address using the emailed token",
)
async def verify_email(
    payload: VerifyEmailRequest,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        await VerifyEmailUseCase(_repo(session)).execute(payload.token)
        await session.commit()
        return {"message": "Email verified successfully."}
    except UnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ─── Admin / User Management (requires ADMIN role) ────────────────────────────

@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="[Admin] List all users",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_async_session),
):
    results = await ListUsersUseCase(_repo(session)).execute(skip=skip, limit=limit)
    return [UserResponse(**r.__dict__) for r in results]


class AssignRoleRequest(BaseModel):
    role: UserRole


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="[Admin] Assign a role to a user",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def assign_role(
    user_id: str,
    payload: AssignRoleRequest,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await AssignRoleUseCase(_repo(session)).execute(user_id, payload.role)
        await session.commit()
        return UserResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/users/{user_id}/deactivate",
    response_model=UserResponse,
    summary="[Admin] Deactivate a user account",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def deactivate_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await DeactivateUserUseCase(_repo(session)).execute(user_id)
        await session.commit()
        return UserResponse(**result.__dict__)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

