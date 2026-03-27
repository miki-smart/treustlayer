"""
SessionService — cross-module public interface.
Auth module calls this to create/validate/revoke refresh tokens.
Also subscribes to ConsentRevokedEvent to cascade revocations.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.core.config import settings
from app.core.security import generate_secure_token, hash_secret
from app.modules.session.domain.entities.refresh_token import RefreshToken
from app.modules.session.domain.repositories.refresh_token_repository import RefreshTokenRepository


class SessionService:
    def __init__(self, refresh_token_repository: RefreshTokenRepository) -> None:
        self._repo = refresh_token_repository

    async def create_refresh_token(
        self,
        user_id: str,
        client_id: str,
        scopes: List[str],
    ) -> str:
        """Create a new refresh token and return the raw (unhashed) value."""
        raw_token = generate_secure_token(48)
        token_hash = hash_secret(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        record = RefreshToken(
            user_id=user_id,
            client_id=client_id,
            scopes=scopes,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        await self._repo.create(record)
        return raw_token

    async def validate_refresh_token(
        self, raw_token: str
    ) -> Optional[RefreshToken]:
        """Validate raw token; return record if valid, None otherwise."""
        if not raw_token:
            return None
        token_hash = hash_secret(raw_token)
        record = await self._repo.get_by_hash(token_hash)
        if not record or not record.is_valid():
            return None
        return record

    async def revoke_refresh_token(self, raw_token: str) -> None:
        token_hash = hash_secret(raw_token)
        await self._repo.revoke_by_hash(token_hash)

    async def revoke_all_for_user_client(
        self, user_id: str, client_id: str
    ) -> None:
        """Called when consent is revoked for a specific client."""
        await self._repo.revoke_all_for_user_client(user_id, client_id)

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._repo.revoke_all_for_user(user_id)
