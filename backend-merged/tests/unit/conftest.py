"""
Pytest configuration and fixtures for unit tests.
"""
import pytest
from datetime import datetime, timezone

from app.modules.identity.domain.entities.user import User, UserRole
from app.modules.app_registry.domain.entities.app import App


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        id="test-user-123",
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2J8T5LZoYe",
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True,
        phone_verified=False,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return User(
        id="admin-user-123",
        email="admin@example.com",
        username="admin",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2J8T5LZoYe",
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True,
    )


@pytest.fixture
def kyc_approver_user():
    """Create a KYC approver user."""
    return User(
        id="kyc-approver-123",
        email="kyc@example.com",
        username="kycapprover",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2J8T5LZoYe",
        role=UserRole.KYC_APPROVER,
        is_active=True,
        is_email_verified=True,
    )


@pytest.fixture
def app_owner_user():
    """Create an app owner user."""
    return User(
        id="app-owner-123",
        email="owner@example.com",
        username="appowner",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2J8T5LZoYe",
        role=UserRole.APP_OWNER,
        is_active=True,
        is_email_verified=True,
    )


@pytest.fixture
def test_app():
    """Create a test OAuth2 app."""
    return App(
        id="test-app-123",
        name="Test Application",
        owner_id="app-owner-123",
        client_id="test-client-id",
        client_secret_hash="hashed-secret",
        api_key_hash="hashed-api-key",
        allowed_scopes=["openid", "profile", "email"],
        redirect_uris=["http://localhost:3000/callback"],
        description="Test app for unit tests",
        category="testing",
        is_active=True,
        is_approved=True,
        is_public=False,
    )
