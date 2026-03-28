"""Tests for trust API response mapping."""
from datetime import datetime, timezone

import pytest

from app.modules.identity.domain.entities.user import User, UserRole
from app.modules.trust.domain.entities.trust_profile import TrustProfile
from app.modules.trust.presentation.helpers.trust_profile_response import build_trust_profile_response


@pytest.fixture
def sample_user() -> User:
    return User(
        id="u1",
        email="a@b.com",
        username="u",
        hashed_password="x",
        role=UserRole.USER,
        is_email_verified=True,
        phone_verified=True,
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_build_trust_profile_response_maps_user_and_risk(sample_user: User):
    profile = TrustProfile(user_id=sample_user.id)
    profile.update_score(
        email_verified=True,
        phone_verified=True,
        kyc_tier=2,
        face_verified=True,
        voice_verified=False,
        digital_identity_active=False,
        account_age_days=10,
    )
    resp = build_trust_profile_response(profile, sample_user)
    assert resp.user_id == sample_user.id
    assert resp.email_verified is True
    assert resp.phone_verified is True
    assert resp.face_verified is True
    assert resp.risk_level in ("low", "medium", "high")
    assert resp.account_age_days >= 0
    assert "T" in resp.last_calculated_at or "-" in resp.last_calculated_at
