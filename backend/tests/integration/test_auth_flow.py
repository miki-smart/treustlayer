"""
Integration tests for the full OIDC auth flow.

Flow under test:
  1.  Register + approve an OAuth2 app
  2.  Register a user
  3.  Submit + approve KYC
  4.  POST /auth/authorize → get authorization code
  5.  POST /auth/token     → exchange code for tokens
  6.  GET  /auth/userinfo  → verify claims
  7.  POST /auth/introspect → verify active + trust_score

Note: These tests use the in-memory SQLite fixture from tests/integration/conftest.py.
      PostgreSQL-specific schemas are flattened via schema_translate_map.
"""
import base64
import hashlib
import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _pkce_pair():
    """Return (code_verifier, code_challenge_S256)."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


@pytest.fixture
def app_payload():
    return {
        "name": "TestClient",
        "allowed_scopes": ["openid", "profile.basic", "profile.email", "kyc.read", "offline_access"],
        "redirect_uris": ["https://example.com/callback"],
        "description": "Integration test OAuth2 client",
    }


@pytest.fixture
def user_payload():
    return {
        "email": "authtest@example.com",
        "username": "authtest",
        "password": "SecurePass123!",
        "full_name": "Auth Test User",
    }


class TestOIDCAuthFlow:
    async def test_full_oidc_flow(
        self,
        integration_client: AsyncClient,
        app_payload: dict,
        user_payload: dict,
    ):
        # ── Step 1: Register OAuth2 app ───────────────────────────────────────
        reg_resp = await integration_client.post("/api/v1/apps/", json=app_payload)
        assert reg_resp.status_code == 201, reg_resp.text
        app_data = reg_resp.json()
        client_id = app_data["client_id"]
        client_secret = app_data["client_secret"]
        assert client_secret is not None  # returned only on creation
        app_id = app_data["id"]

        # ── Step 2: Approve the app ───────────────────────────────────────────
        approve_resp = await integration_client.post(f"/api/v1/apps/{app_id}/approve")
        assert approve_resp.status_code == 200, approve_resp.text

        # ── Step 3: Register a user ───────────────────────────────────────────
        user_resp = await integration_client.post("/api/v1/identity/register", json=user_payload)
        assert user_resp.status_code == 201, user_resp.text
        user_id = user_resp.json()["id"]

        # ── Step 4: Submit KYC ────────────────────────────────────────────────
        kyc_submit_resp = await integration_client.post(
            f"/api/v1/kyc/submit/{user_id}",
            json={
                "document_type": "passport",
                "document_number": "AB123456",
                "document_url": "https://s3.example.com/doc.jpg",
                "face_image_url": "https://s3.example.com/face.jpg",
            },
        )
        assert kyc_submit_resp.status_code == 202, kyc_submit_resp.text
        kyc_id = kyc_submit_resp.json()["id"]

        # ── Step 5: Approve KYC ───────────────────────────────────────────────
        kyc_approve_resp = await integration_client.post(f"/api/v1/kyc/{kyc_id}/approve")
        assert kyc_approve_resp.status_code == 200, kyc_approve_resp.text
        kyc_data = kyc_approve_resp.json()
        assert kyc_data["status"] == "approved"
        assert kyc_data["trust_score"] > 0

        # ── Step 6: Authorize (get auth code) ─────────────────────────────────
        verifier, challenge = _pkce_pair()
        authorize_resp = await integration_client.post(
            "/api/v1/auth/authorize",
            json={
                "username": user_payload["username"],
                "password": user_payload["password"],
                "client_id": client_id,
                "redirect_uri": "https://example.com/callback",
                "scope": "openid profile.basic profile.email kyc.read offline_access",
                "state": "xyz-state-123",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        assert authorize_resp.status_code == 200, authorize_resp.text
        auth_data = authorize_resp.json()
        assert "code" in auth_data
        assert auth_data["state"] == "xyz-state-123"
        code = auth_data["code"]

        # ── Step 7: Exchange code for tokens ─────────────────────────────────
        token_resp = await integration_client.post(
            "/api/v1/auth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": "https://example.com/callback",
                "code_verifier": verifier,
            },
        )
        assert token_resp.status_code == 200, token_resp.text
        token_data = token_resp.json()
        assert token_data["token_type"] == "Bearer"
        assert "access_token" in token_data
        assert "refresh_token" in token_data  # offline_access requested
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]

        # ── Step 8: GET /userinfo ─────────────────────────────────────────────
        userinfo_resp = await integration_client.get(
            "/api/v1/auth/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert userinfo_resp.status_code == 200, userinfo_resp.text
        userinfo = userinfo_resp.json()
        assert userinfo["sub"] == user_id
        assert userinfo["username"] == user_payload["username"]
        assert userinfo["email"] == user_payload["email"]

        # ── Step 9: POST /introspect ──────────────────────────────────────────
        introspect_resp = await integration_client.post(
            "/api/v1/auth/introspect",
            json={
                "token": access_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        assert introspect_resp.status_code == 200, introspect_resp.text
        introspect_data = introspect_resp.json()
        assert introspect_data["active"] is True
        assert introspect_data["sub"] == user_id
        assert introspect_data["trust_score"] > 0

        # ── Step 10: Refresh token rotation ───────────────────────────────────
        refresh_resp = await integration_client.post(
            "/api/v1/auth/token",
            json={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            },
        )
        assert refresh_resp.status_code == 200, refresh_resp.text
        refreshed = refresh_resp.json()
        assert "access_token" in refreshed
        # Old refresh token must be rotated (new one issued)
        assert refreshed.get("refresh_token") != refresh_token

    async def test_authorize_wrong_password_returns_401(
        self,
        integration_client: AsyncClient,
        app_payload: dict,
        user_payload: dict,
    ):
        # Register + approve app, register user first
        reg = await integration_client.post("/api/v1/apps/", json=app_payload)
        assert reg.status_code == 201
        client_id = reg.json()["client_id"]
        await integration_client.post(f"/api/v1/apps/{reg.json()['id']}/approve")
        await integration_client.post("/api/v1/identity/register", json=user_payload)

        resp = await integration_client.post(
            "/api/v1/auth/authorize",
            json={
                "username": user_payload["username"],
                "password": "wrong-password",
                "client_id": client_id,
                "redirect_uri": "https://example.com/callback",
                "scope": "openid",
            },
        )
        assert resp.status_code == 401

    async def test_token_exchange_invalid_code_returns_400(
        self,
        integration_client: AsyncClient,
        app_payload: dict,
    ):
        reg = await integration_client.post("/api/v1/apps/", json=app_payload)
        assert reg.status_code == 201
        app_data = reg.json()
        await integration_client.post(f"/api/v1/apps/{app_data['id']}/approve")

        resp = await integration_client.post(
            "/api/v1/auth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": app_data["client_id"],
                "client_secret": app_data["client_secret"],
                "code": "invalid-code-xyz",
                "redirect_uri": "https://example.com/callback",
            },
        )
        assert resp.status_code in (400, 404)
