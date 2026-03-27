"""
Email verification use cases: send verification email, verify email token.
"""
from datetime import datetime, timedelta, timezone

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import generate_secure_token, hash_secret
from app.infrastructure.external.email_service import email_service
from app.modules.identity.domain.repositories.user_repository import UserRepository

_EMAIL_VERIFY_TOKEN_TTL_MINUTES = 60


class SendEmailVerificationUseCase:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> None:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        if user.is_email_verified:
            return  # already verified — no-op

        token = generate_secure_token()
        token_hash = hash_secret(token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=_EMAIL_VERIFY_TOKEN_TTL_MINUTES)

        await self._repo.set_email_verification_token(user.id, token_hash, expires_at)
        await email_service.send_verification_email(user.email, token)


class VerifyEmailUseCase:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, token: str) -> None:
        token_hash = hash_secret(token)
        user = await self._repo.get_by_email_verification_token_hash(token_hash)
        if not user:
            raise UnauthorizedError("Invalid or expired verification token")

        if (
            user.email_verification_expires_at is not None
            and datetime.now(timezone.utc) > user.email_verification_expires_at
        ):
            raise UnauthorizedError("Verification token has expired")

        user.verify_email()
        await self._repo.update(user)
        await self._repo.clear_email_verification_token(user.id)
