from typing import Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.session.domain.entities.refresh_token import RefreshToken
from app.modules.session.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.modules.session.infrastructure.persistence.refresh_token_model import RefreshTokenModel


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        model = RefreshTokenModel(
            id=token.id,
            token_hash=token.token_hash,
            user_id=token.user_id,
            client_id=token.client_id,
            scopes=token.scopes,
            is_revoked=token.is_revoked,
            expires_at=token.expires_at,
            created_at=token.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self._session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def revoke_by_hash(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await self._session.flush()

    async def revoke_all_for_user_client(
        self, user_id: str, client_id: str
    ) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(
                and_(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.client_id == client_id,
                    RefreshTokenModel.is_revoked.is_(False),
                )
            )
            .values(is_revoked=True)
        )
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(
                and_(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.is_revoked.is_(False),
                )
            )
            .values(is_revoked=True)
        )
        await self._session.flush()

    async def revoke_by_id(self, token_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id)
            .values(is_revoked=True)
        )
        await self._session.flush()

    async def list_active_for_user(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> list[RefreshToken]:
        from sqlalchemy import select as sa_select
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            sa_select(RefreshTokenModel)
            .where(
                and_(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.is_revoked.is_(False),
                    RefreshTokenModel.expires_at > now,
                )
            )
            .order_by(RefreshTokenModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    @staticmethod
    def _to_entity(model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=str(model.id),
            token_hash=str(model.token_hash),
            user_id=str(model.user_id),
            client_id=str(model.client_id),
            scopes=list(model.scopes or []),
            is_revoked=bool(model.is_revoked),
            expires_at=model.expires_at,
            created_at=model.created_at,
        )
