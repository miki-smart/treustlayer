"""
Identity management — /api/v1/identity/*
Covers user registration, profile, password, email verification, and admin user ops.
"""
import uuid
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, AdminUser, DB
from app.models.user import User, UserRole
from app.models.tokens import PasswordResetToken, EmailVerificationToken
from app.utils.security import hash_password, verify_password
from app.utils.audit import write_audit_entry

router = APIRouter(prefix="/identity", tags=["Identity"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserRegistrationRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None
    phone_number: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str
    full_name: str | None = None
    phone_number: str | None = None
    is_active: bool
    is_email_verified: bool
    created_at: str

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class AssignRoleRequest(BaseModel):
    role: UserRole


def _user_out(u: User) -> UserResponse:
    return UserResponse(
        id=str(u.id),
        email=u.email,
        username=u.username or u.email.split("@")[0],
        role=u.role,
        full_name=u.name,
        phone_number=u.phone,
        is_active=u.is_active,
        is_email_verified=u.email_verified,
        created_at=u.created_at.isoformat() if u.created_at else "",
    )


# ── Registration ──────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=201, summary="Register a new user")
async def register_user(body: UserRegistrationRequest, db: DB):
    # Check uniqueness
    existing = (await db.execute(
        select(User).where(or_(User.email == body.email, User.username == body.username))
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email or username already registered")

    user = User(
        id=uuid.uuid4(),
        name=body.full_name or body.username,
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        phone=body.phone_number,
        role=UserRole.user,
        is_active=True,
        email_verified=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    await write_audit_entry(db, action="User Registered", actor_id=user.id, actor_name=user.name, target=user.email, details="New user account created")
    return _user_out(user)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/users/me", response_model=UserResponse, summary="Get current user's own profile")
async def get_my_profile(current_user: CurrentUser):
    return _user_out(current_user)


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user profile")
async def get_user(user_id: str, current_user: CurrentUser, db: DB):
    if str(current_user.id) != user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_out(user)


@router.patch("/users/{user_id}", response_model=UserResponse, summary="Update user profile")
async def update_user(user_id: str, body: UserUpdateRequest, current_user: CurrentUser, db: DB):
    if str(current_user.id) != user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.name = body.full_name
    if body.phone_number is not None:
        user.phone = body.phone_number
    return _user_out(user)


# ── Password ──────────────────────────────────────────────────────────────────

@router.post("/forgot-password", status_code=202, summary="Request a password-reset email")
async def forgot_password(body: ForgotPasswordRequest, db: DB):
    """Always returns 202 — never reveals whether the email exists."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=2)
        db.add(PasswordResetToken(
            id=uuid.uuid4(), user_id=user.id, token=token,
            expires_at=expires, used=False,
        ))
        # In production: send email with reset link
        # For demo: token is returned in logs
        print(f"[DEV] Password reset token for {user.email}: {token}")
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", summary="Reset password using the emailed token")
async def reset_password(body: ResetPasswordRequest, db: DB):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == body.token,
            PasswordResetToken.used == False,
        )
    )
    prt = result.scalar_one_or_none()
    if not prt or prt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    prt.used = True
    user_result = await db.execute(select(User).where(User.id == prt.user_id))
    user = user_result.scalar_one()
    user.hashed_password = hash_password(body.new_password)
    return {"message": "Password reset successfully"}


@router.post("/users/{user_id}/change-password", summary="Change own password (authenticated)")
async def change_password(user_id: str, body: ChangePasswordRequest, current_user: CurrentUser, db: DB):
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot change another user's password")
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(body.new_password)
    return {"message": "Password changed successfully"}


# ── Email Verification ────────────────────────────────────────────────────────

@router.post("/send-verification-email", status_code=202, summary="Send (or resend) an email-verification link")
async def send_verification_email(current_user: CurrentUser, db: DB):
    if current_user.email_verified:
        return {"message": "Email is already verified"}
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.add(EmailVerificationToken(
        id=uuid.uuid4(), user_id=current_user.id, token=token,
        expires_at=expires, used=False,
    ))
    print(f"[DEV] Email verification token for {current_user.email}: {token}")
    return {"message": "Verification email sent"}


@router.post("/verify-email", summary="Verify email address using the emailed token")
async def verify_email(body: VerifyEmailRequest, db: DB):
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == body.token,
            EmailVerificationToken.used == False,
        )
    )
    evt = result.scalar_one_or_none()
    if not evt or evt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    evt.used = True
    user_result = await db.execute(select(User).where(User.id == evt.user_id))
    user = user_result.scalar_one()
    user.email_verified = True
    return {"message": "Email verified successfully"}


# ── Admin: User Management ────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse], summary="[Admin] List all users")
async def list_users(
    current_user: AdminUser, db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    result = await db.execute(select(User).offset(skip).limit(limit).order_by(User.created_at.desc()))
    return [_user_out(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}/role", response_model=UserResponse, summary="[Admin] Assign a role to a user")
async def assign_role(user_id: str, body: AssignRoleRequest, current_user: AdminUser, db: DB):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = body.role
    await write_audit_entry(db, action="Role Assigned", actor_id=current_user.id, actor_name=current_user.name, target=user.email, details=f"Role set to {body.role}")
    return _user_out(user)


@router.post("/users/{user_id}/deactivate", response_model=UserResponse, summary="[Admin] Deactivate a user account")
async def deactivate_user(user_id: str, current_user: AdminUser, db: DB):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await write_audit_entry(db, action="User Deactivated", actor_id=current_user.id, actor_name=current_user.name, target=user.email, details="Account deactivated by admin")
    return _user_out(user)
