"""
Integration tests for OIDC Authorization Code Flow.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_oidc_flow(client: AsyncClient, test_user, test_app):
    """
    Test complete OIDC authorization code flow.
    
    Steps:
    1. Authorize (get authorization code)
    2. Exchange code for tokens
    3. Get userinfo with access token
    4. Introspect token
    5. Refresh access token
    """
    # Step 1: Authorize
    auth_response = await client.post(
        "/api/v1/auth/authorize",
        json={
            "email": test_user.email,
            "password": "password123",
            "client_id": test_app.client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "scopes": ["openid", "profile", "email"],
            "state": "xyz123",
        },
    )
    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    assert "code" in auth_data
    code = auth_data["code"]
    
    # Step 2: Exchange token
    token_response = await client.post(
        "/api/v1/auth/token",
        json={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": test_app.client_id,
            "client_secret": "test_secret",
            "redirect_uri": "http://localhost:3000/callback",
        },
    )
    assert token_response.status_code == 200
    tokens = token_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert "id_token" in tokens
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 900
    
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # Step 3: Get userinfo
    userinfo_response = await client.get(
        "/api/v1/auth/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert userinfo_response.status_code == 200
    userinfo = userinfo_response.json()
    assert userinfo["email"] == test_user.email
    assert userinfo["sub"] == test_user.id
    
    # Step 4: Introspect token
    introspect_response = await client.post(
        "/api/v1/auth/introspect", json={"token": access_token}
    )
    assert introspect_response.status_code == 200
    introspect_data = introspect_response.json()
    assert introspect_data["active"] is True
    assert introspect_data["sub"] == test_user.id
    
    # Step 5: Refresh access token
    refresh_response = await client.post(
        "/api/v1/auth/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": test_app.client_id,
            "client_secret": "test_secret",
        },
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != access_token


@pytest.mark.asyncio
async def test_oidc_discovery(client: AsyncClient):
    """Test OIDC discovery document."""
    response = await client.get("/api/v1/auth/.well-known/openid-configuration")
    assert response.status_code == 200
    
    config = response.json()
    assert config["issuer"] == "http://localhost:8000"
    assert "authorization_endpoint" in config
    assert "token_endpoint" in config
    assert "userinfo_endpoint" in config
    assert "jwks_uri" in config
    assert "code" in config["response_types_supported"]
    assert "authorization_code" in config["grant_types_supported"]


@pytest.mark.asyncio
async def test_jwks_endpoint(client: AsyncClient):
    """Test JWKS endpoint."""
    response = await client.get("/api/v1/auth/.well-known/jwks.json")
    assert response.status_code == 200
    
    jwks = response.json()
    assert "keys" in jwks
    assert len(jwks["keys"]) > 0
    key = jwks["keys"][0]
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert key["alg"] == "RS256"


@pytest.mark.asyncio
async def test_pkce_flow(client: AsyncClient, test_user, test_app):
    """Test OIDC flow with PKCE."""
    import base64
    import hashlib
    import secrets
    
    # Generate PKCE challenge
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    
    # Authorize with PKCE
    auth_response = await client.post(
        "/api/v1/auth/authorize",
        json={
            "email": test_user.email,
            "password": "password123",
            "client_id": test_app.client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "scopes": ["openid", "profile"],
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
    )
    assert auth_response.status_code == 200
    code = auth_response.json()["code"]
    
    # Exchange with code_verifier
    token_response = await client.post(
        "/api/v1/auth/token",
        json={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": test_app.client_id,
            "client_secret": "test_secret",
            "redirect_uri": "http://localhost:3000/callback",
            "code_verifier": code_verifier,
        },
    )
    assert token_response.status_code == 200
    tokens = token_response.json()
    assert "access_token" in tokens
