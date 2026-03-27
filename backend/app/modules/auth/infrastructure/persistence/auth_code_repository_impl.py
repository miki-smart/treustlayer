from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.repositories.auth_code_repository import AuthCodeRepository
from app.modules.auth.infrastructure.persistence.auth_code_model import AuthorizationCodeModel


class SQLAlchemyAuthCodeRepository(AuthCodeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, code: AuthorizationCode) -> AuthorizationCode:
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
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_code(self, code: str) -> Optional[AuthorizationCode]:
        result = await self._session.execute(
            select(AuthorizationCodeModel).where(AuthorizationCodeModel.code == code)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def consume(self, code: str) -> None:
        await self._session.execute(
            update(AuthorizationCodeModel)
            .where(AuthorizationCodeModel.code == code)
            .values(is_used=True)
        )
        await self._session.flush()

    @staticmethod
    def _to_entity(model: AuthorizationCodeModel) -> AuthorizationCode:
        return AuthorizationCode(
            id=str(model.id),
            code=str(model.code),
            client_id=str(model.client_id),
            user_id=str(model.user_id),
            redirect_uri=str(model.redirect_uri),
            scopes=list(model.scopes or []),
            code_challenge=model.code_challenge,
            code_challenge_method=model.code_challenge_method,
            expires_at=model.expires_at,
            is_used=bool(model.is_used),
        )
