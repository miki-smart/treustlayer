"""
Unit tests for the Consent domain entity and ConsentService.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.modules.consent.domain.entities.consent import Consent
from app.modules.consent.application.services.consent_service import ConsentService


class TestConsentEntity:
    def test_covers_all_requested_scopes(self):
        consent = Consent(
            user_id="u1", client_id="c1", scopes=["openid", "profile.basic", "kyc.read"]
        )
        assert consent.covers_scopes(["openid"]) is True
        assert consent.covers_scopes(["openid", "profile.basic"]) is True

    def test_missing_scope_returns_false(self):
        consent = Consent(user_id="u1", client_id="c1", scopes=["openid"])
        assert consent.covers_scopes(["openid", "profile.email"]) is False

    def test_revoke_sets_inactive(self):
        consent = Consent(user_id="u1", client_id="c1", scopes=["openid"])
        consent.revoke()
        assert consent.is_active is False
        assert consent.revoked_at is not None


class TestConsentService:
    @pytest.mark.asyncio
    async def test_has_consent_true_when_covered(self):
        existing = Consent(user_id="u1", client_id="c1", scopes=["openid", "profile.basic"])
        repo = AsyncMock()
        repo.get_active.return_value = existing

        service = ConsentService(repo)
        result = await service.has_consent("u1", "c1", ["openid"])
        assert result is True

    @pytest.mark.asyncio
    async def test_has_consent_false_when_missing_scope(self):
        existing = Consent(user_id="u1", client_id="c1", scopes=["openid"])
        repo = AsyncMock()
        repo.get_active.return_value = existing

        service = ConsentService(repo)
        result = await service.has_consent("u1", "c1", ["openid", "kyc.read"])
        assert result is False

    @pytest.mark.asyncio
    async def test_has_consent_false_when_no_record(self):
        repo = AsyncMock()
        repo.get_active.return_value = None

        service = ConsentService(repo)
        assert await service.has_consent("u1", "c1", ["openid"]) is False

    @pytest.mark.asyncio
    async def test_grant_consent_creates_new(self):
        repo = AsyncMock()
        repo.get_active.return_value = None
        repo.create.side_effect = lambda c: c

        service = ConsentService(repo)
        with patch("app.modules.consent.application.services.consent_service.event_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            consent = await service.grant_consent("u1", "c1", ["openid", "profile.basic"])

        repo.create.assert_called_once()
        assert set(consent.scopes) == {"openid", "profile.basic"}
        mock_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_grant_consent_merges_existing(self):
        existing = Consent(user_id="u1", client_id="c1", scopes=["openid"])
        repo = AsyncMock()
        repo.get_active.return_value = existing
        repo.update.side_effect = lambda c: c

        service = ConsentService(repo)
        with patch("app.modules.consent.application.services.consent_service.event_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            consent = await service.grant_consent("u1", "c1", ["profile.basic"])

        repo.update.assert_called_once()
        assert "openid" in consent.scopes
        assert "profile.basic" in consent.scopes

    @pytest.mark.asyncio
    async def test_revoke_consent_publishes_event(self):
        existing = Consent(user_id="u1", client_id="c1", scopes=["openid"])
        repo = AsyncMock()
        repo.get_active.return_value = existing
        repo.revoke = AsyncMock()

        service = ConsentService(repo)
        with patch("app.modules.consent.application.services.consent_service.event_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            await service.revoke_consent("u1", "c1")

        repo.revoke.assert_called_once_with(existing.id)
        mock_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_consent_no_op_when_missing(self):
        repo = AsyncMock()
        repo.get_active.return_value = None

        service = ConsentService(repo)
        with patch("app.modules.consent.application.services.consent_service.event_bus") as mock_bus:
            mock_bus.publish = AsyncMock()
            await service.revoke_consent("u1", "c1")

        repo.revoke.assert_not_called()
        mock_bus.publish.assert_not_called()
