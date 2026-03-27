"""
Unit tests for domain entities and use cases.
These tests run with no DB — pure domain logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.application.use_cases.register_user import RegisterUserUseCase
from app.modules.identity.application.dto.user_dto import RegisterUserDTO
from app.core.exceptions import ConflictError


# ── Email value object ────────────────────────────────────────────────────────

class TestEmailValueObject:
    def test_valid_email(self):
        email = Email("user@example.com")
        assert str(email) == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError):
            Email("not-an-email")

    def test_email_case_preserved(self):
        email = Email("User@Example.COM")
        assert email.value == "User@Example.COM"

    def test_email_is_frozen(self):
        email = Email("user@test.com")
        with pytest.raises(Exception):
            email.value = "other@test.com"  # type: ignore


# ── User entity ───────────────────────────────────────────────────────────────

class TestUserEntity:
    def test_user_created_active(self):
        user = User(email="a@b.com", username="alice", hashed_password="hashed")
        assert user.is_active is True
        assert user.is_email_verified is False

    def test_deactivate_user(self):
        user = User(email="a@b.com", username="alice", hashed_password="hashed")
        user.deactivate()
        assert user.is_active is False

    def test_verify_email(self):
        user = User(email="a@b.com", username="alice", hashed_password="hashed")
        user.verify_email()
        assert user.is_email_verified is True

    def test_update_profile(self):
        user = User(email="a@b.com", username="alice", hashed_password="hashed")
        user.update_profile(full_name="Alice Smith", phone_number="+1234567890")
        assert user.full_name == "Alice Smith"
        assert user.phone_number == "+1234567890"

    def test_update_profile_preserves_none_unchanged(self):
        user = User(email="a@b.com", username="alice", hashed_password="hashed", full_name="Alice")
        user.update_profile(phone_number="+9999")
        assert user.full_name == "Alice"  # unchanged


# ── RegisterUserUseCase ───────────────────────────────────────────────────────

class TestRegisterUserUseCase:
    @pytest.mark.asyncio
    async def test_register_new_user_succeeds(self):
        repo = AsyncMock()
        repo.exists_by_email.return_value = False
        repo.exists_by_username.return_value = False
        repo.create.side_effect = lambda user: user

        use_case = RegisterUserUseCase(repo)
        result = await use_case.execute(
            RegisterUserDTO(
                email="alice@example.com",
                username="alice",
                password="securepassword",
            )
        )

        assert result.email == "alice@example.com"
        assert result.username == "alice"
        repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self):
        repo = AsyncMock()
        repo.exists_by_email.return_value = True

        use_case = RegisterUserUseCase(repo)
        with pytest.raises(ConflictError, match="already registered"):
            await use_case.execute(
                RegisterUserDTO(
                    email="alice@example.com",
                    username="alice",
                    password="securepassword",
                )
            )

    @pytest.mark.asyncio
    async def test_register_duplicate_username_raises(self):
        repo = AsyncMock()
        repo.exists_by_email.return_value = False
        repo.exists_by_username.return_value = True

        use_case = RegisterUserUseCase(repo)
        with pytest.raises(ConflictError, match="already taken"):
            await use_case.execute(
                RegisterUserDTO(
                    email="alice@example.com",
                    username="alice",
                    password="securepassword",
                )
            )
