"""
Password management use cases: forgot-password, reset-password, change-password.
"""
from datetime import datetime, timedelta, timezone

from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.core.security import (
    generate_secure_token,
    hash_password,
    hash_secret,
    verify_password,
)
from app.infrastructure.external.email_service import email_service
from app.modules.identity.domain.repositories.user_repository import UserRepository

_RESET_TOKEN_TTL_MINUTES = 30


class ForgotPasswordUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, email: str) -> None:
        """
        Generate a one-time password-reset token, persist its hash, and email it.
        We return success regardless of whether the email exists, to avoid
        user enumeration attacks.
        """
        user = await self._repo.get_by_email(email.lower())
        if not user:
            return

        raw_token = generate_secure_token(32)
        token_hash = hash_secret(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=_RESET_TOKEN_TTL_MINUTES)

        await self._repo.set_password_reset_token(user.id, token_hash, expires_at)
        await email_service.send_password_reset_email(user.email, raw_token)


class ResetPasswordUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, token: str, new_password: str) -> None:
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        token_hash = hash_secret(token)
        user = await self._repo.get_by_reset_token_hash(token_hash)
        if not user:
            raise UnauthorizedError("Invalid or expired password reset token")

        user.set_password(hash_password(new_password))
        await self._repo.update(user)
        await self._repo.clear_password_reset_token(user.id)


class ChangePasswordUseCase:
    def __init__(self, user_repository: UserRepository) -> None:
        self._repo = user_repository

    async def execute(self, user_id: str, current_password: str, new_password: str) -> None:
        if len(new_password) < 8:
            raise ValidationError("New password must be at least 8 characters")

        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")

        user.set_password(hash_password(new_password))
        await self._repo.update(user)
