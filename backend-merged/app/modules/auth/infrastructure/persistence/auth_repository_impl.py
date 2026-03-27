"""
SQLAlchemy implementation of AuthRepository.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.domain.repositories.auth_repository import AuthRepository
from app.modules.auth.infrastructure.persistence.auth_model import (
    AuthorizationCodeModel,
    RefreshTokenModel,
)


class SQLAlchemyAuthRepository(AuthRepository):
    """SQLAlchemy implementation of auth repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_authorization_code(
        self, code: AuthorizationCode
    ) -> AuthorizationCode:
        """Save authorization code."""
        model = AuthorizationCodeModel(
            id=code.id,
            code=code.code,
            client_id=code.client_id,
            user_id=code.user_id,
            redirect_uri=code.redirect_uri,
            scopes=code.scopes,
            code_challenge=code.code_challenge,
            code_challenge_method=code.code_challenge_method,
            expires_at=code.expires_at,
            is_used=code.is_used,
        )
        self.session.add(model)
        await self.session.flush()
        return code
    
    async def get_authorization_code(self, code: str) -> Optional[AuthorizationCode]:
        """Retrieve authorization code by code value."""
        result = await self.session.execute(
            select(AuthorizationCodeModel).where(AuthorizationCodeModel.code == code)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        
        return AuthorizationCode(
            id=str(model.id),
            code=model.code,
            client_id=model.client_id,
            user_id=str(model.user_id),
            redirect_uri=model.redirect_uri,
            scopes=model.scopes,
            code_challenge=model.code_challenge,
            code_challenge_method=model.code_challenge_method,
            expires_at=model.expires_at,
            is_used=model.is_used,
        )
    
    async def mark_code_as_used(self, code: str) -> None:
        """Mark authorization code as used."""
        await self.session.execute(
            update(AuthorizationCodeModel)
            .where(AuthorizationCodeModel.code == code)
            .values(is_used=True)
        )
        await self.session.flush()
    
    async def save_refresh_token(self, token: RefreshToken) -> RefreshToken:
        """Save or update refresh token."""
        # Check if token exists
        result = await self.session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.id == token.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.last_used_at = token.last_used_at
            existing.is_revoked = token.is_revoked
        else:
            # Create new
            model = RefreshTokenModel(
                id=token.id,
                user_id=token.user_id,
                client_id=token.client_id,
                token_hash=token.token_hash,
                scopes=token.scopes,
                expires_at=token.expires_at,
                is_revoked=token.is_revoked,
                device_info=token.device_info,
                ip_address=token.ip_address,
                created_at=token.created_at,
                last_used_at=token.last_used_at,
            )
            self.session.add(model)
        
        await self.session.flush()
        return token
    
    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve refresh token by hash."""
        result = await self.session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        
        return RefreshToken(
            id=str(model.id),
            user_id=str(model.user_id),
            client_id=model.client_id,
            token_hash=model.token_hash,
            scopes=model.scopes,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
            device_info=model.device_info,
            ip_address=model.ip_address,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
        )
    
    async def revoke_refresh_token(self, token_id: str) -> None:
        """Revoke a specific refresh token."""
        await self.session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id)
            .values(is_revoked=True)
        )
        await self.session.flush()
    
    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        await self.session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.session.flush()
    
    async def list_user_tokens(self, user_id: str) -> List[RefreshToken]:
        """List all active refresh tokens for a user."""
        result = await self.session.execute(
            select(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id, RefreshTokenModel.is_revoked == False
            )
            .order_by(RefreshTokenModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]
    
    async def delete_expired_codes(self) -> int:
        """Delete expired authorization codes."""
        result = await self.session.execute(
            delete(AuthorizationCodeModel).where(
                AuthorizationCodeModel.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.flush()
        return result.rowcount
    
    async def delete_expired_tokens(self) -> int:
        """Delete expired refresh tokens."""
        result = await self.session.execute(
            delete(RefreshTokenModel).where(
                RefreshTokenModel.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.flush()
        return result.rowcount
    
    def _model_to_entity(self, model: RefreshTokenModel) -> RefreshToken:
        """Convert model to entity."""
        return RefreshToken(
            id=str(model.id),
            user_id=str(model.user_id),
            client_id=model.client_id,
            token_hash=model.token_hash,
            scopes=model.scopes,
            expires_at=model.expires_at,
            is_revoked=model.is_revoked,
            device_info=model.device_info,
            ip_address=model.ip_address,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
        )
