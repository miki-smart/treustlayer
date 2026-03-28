import pytest
from unittest.mock import AsyncMock

from app.modules.identity.application.use_cases.manual_verify_contact import (
    ManualVerifyEmailUseCase,
    ManualVerifyPhoneUseCase,
)
from app.modules.identity.domain.entities.user import User, UserRole
from app.core.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_manual_verify_email():
    user = User(
        email="a@b.com",
        username="u1",
        hashed_password="x",
        role=UserRole.USER,
        is_email_verified=False,
    )
    user.id = "uid-1"
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    repo.update.side_effect = lambda u: u

    out = await ManualVerifyEmailUseCase(repo).execute("uid-1")
    assert out.is_email_verified is True
    repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_manual_verify_phone_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await ManualVerifyPhoneUseCase(repo).execute("missing")
