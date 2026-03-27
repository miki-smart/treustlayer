"""
OIDC / OAuth2 service.

Implements:
  - Authorization Code Flow (with optional PKCE)
  - Token issuance (access + refresh)
  - UserInfo endpoint
  - Token introspection

For simplicity in the hackathon context, tokens are signed with HMAC-SHA256
using the same SECRET_KEY. In production, use RSA (RS256) with key rotation.

Supported scopes:
  openid, profile, email, phone, address, kyc_status, trust_score
"""
import uuid
import hashlib
import base64
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import HTTPException
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.app_registry import RegisteredApp, AuthorizationCode, UserApp, AppStatus
from app.models.user import User
from app.models.kyc import KYCApplication, KYCStatus
from app.utils.security import verify_password
from app.services import trust_service

# OIDC token issuer identifier
ISSUER = "https://trustlayer-id.local"


# ── PKCE helpers ──────────────────────────────────────────────────────────────

def _verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode()).digest()
        calculated = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return hmac_compare(calculated, code_challenge)
    # plain
    return hmac_compare(code_verifier, code_challenge)


def hmac_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())


# ── Authorization endpoint ────────────────────────────────────────────────────

async def create_authorization_code(
    db: AsyncSession,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    user: User,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
) -> str:
    """Validate client, create and return auth code."""
    result = await db.execute(
        select(RegisteredApp).where(
            RegisteredApp.client_id == client_id,
            RegisteredApp.status == AppStatus.approved,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=400, detail="Invalid or unapproved client_id")

    if redirect_uri not in app.redirect_uris:
        raise HTTPException(status_code=400, detail="redirect_uri not registered for this client")

    # Validate scopes
    invalid = set(scopes) - set(app.allowed_scopes)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Scopes not allowed: {invalid}")

    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    auth_code = AuthorizationCode(
        id=uuid.uuid4(),
        code=code,
        app_id=app.id,
        user_id=user.id,
        scopes=scopes,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method or "S256",
        expires_at=expires_at,
        used=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(auth_code)
    await db.flush()
    return code


# ── Token endpoint ────────────────────────────────────────────────────────────

async def exchange_code_for_tokens(
    db: AsyncSession,
    grant_type: str,
    client_id: str,
    client_secret: str,
    code: str | None = None,
    redirect_uri: str | None = None,
    code_verifier: str | None = None,
    refresh_token: str | None = None,
) -> dict:
    """Handle authorization_code and refresh_token grants."""
    # Validate client
    app_result = await db.execute(
        select(RegisteredApp).where(RegisteredApp.client_id == client_id)
    )
    app = app_result.scalar_one_or_none()
    if not app or not verify_password(client_secret, app.client_secret_hash):
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    if grant_type == "authorization_code":
        return await _handle_code_grant(db, app, code, redirect_uri, code_verifier)
    elif grant_type == "refresh_token":
        return await _handle_refresh_grant(db, app, refresh_token)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {grant_type}")


async def _handle_code_grant(
    db: AsyncSession,
    app: RegisteredApp,
    code: str | None,
    redirect_uri: str | None,
    code_verifier: str | None,
) -> dict:
    if not code:
        raise HTTPException(status_code=400, detail="code is required")

    result = await db.execute(
        select(AuthorizationCode)
        .where(AuthorizationCode.code == code, AuthorizationCode.app_id == app.id)
    )
    auth_code = result.scalar_one_or_none()
    if not auth_code:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    if auth_code.used:
        raise HTTPException(status_code=400, detail="Authorization code already used")
    if auth_code.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Authorization code expired")
    if redirect_uri and auth_code.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="redirect_uri mismatch")

    # PKCE verification
    if auth_code.code_challenge and code_verifier:
        if not _verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method or "S256"):
            raise HTTPException(status_code=400, detail="PKCE verification failed")
    elif auth_code.code_challenge and not code_verifier:
        raise HTTPException(status_code=400, detail="code_verifier required for PKCE flow")

    auth_code.used = True
    user_result = await db.execute(select(User).where(User.id == auth_code.user_id))
    user = user_result.scalar_one()

    return await _build_token_response(db, user, app, auth_code.scopes)


async def _handle_refresh_grant(db: AsyncSession, app: RegisteredApp, refresh_token: str | None) -> dict:
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "oidc_refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    scopes = payload.get("scopes", [])
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return await _build_token_response(db, user, app, scopes)


async def _build_token_response(db: AsyncSession, user: User, app: RegisteredApp, scopes: list[str]) -> dict:
    trust = await trust_service.get_trust_profile(db, user)
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims: dict[str, Any] = {
        "iss": ISSUER,
        "sub": str(user.id),
        "aud": app.client_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "scope": " ".join(scopes),
        "client_id": app.client_id,
    }

    if "openid" in scopes:
        claims["sub"] = str(user.id)
    if "profile" in scopes:
        claims["name"] = user.name
        claims["picture"] = user.avatar
    if "email" in scopes:
        claims["email"] = user.email
        claims["email_verified"] = user.email_verified
    if "phone" in scopes:
        claims["phone"] = user.phone
        claims["phone_verified"] = user.phone_verified
    if "kyc_status" in scopes:
        claims["kyc_tier"] = trust.kyc_tier
    if "trust_score" in scopes:
        claims["trust_score"] = trust.trust_score

    access_token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Refresh token (longer lived)
    refresh_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_claims = {
        "iss": ISSUER,
        "sub": str(user.id),
        "aud": app.client_id,
        "type": "oidc_refresh",
        "scopes": scopes,
        "exp": int(refresh_exp.timestamp()),
    }
    refresh = jwt.encode(refresh_claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # ID token (if openid scope)
    id_token = None
    if "openid" in scopes:
        id_claims = {**claims, "nonce": secrets.token_hex(8)}
        id_token = jwt.encode(id_claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # Mark user as connected to app
    existing_conn = await db.execute(
        select(UserApp).where(UserApp.user_id == user.id, UserApp.app_id == app.id)
    )
    conn = existing_conn.scalar_one_or_none()
    if conn:
        conn.last_used = now
    else:
        db.add(UserApp(
            id=uuid.uuid4(),
            user_id=user.id,
            app_id=app.id,
            connected_at=now,
            last_used=now,
        ))

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(exp.timestamp()) - int(now.timestamp()),
        "refresh_token": refresh,
        "id_token": id_token,
        "scope": " ".join(scopes),
    }


# ── UserInfo endpoint ─────────────────────────────────────────────────────────

async def get_userinfo(db: AsyncSession, token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_aud": False})
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    user_id = payload.get("sub")
    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    scopes = payload.get("scope", "").split()
    trust = await trust_service.get_trust_profile(db, user)

    info: dict = {"sub": str(user.id)}
    if "profile" in scopes:
        info["name"] = user.name
        info["picture"] = user.avatar
    if "email" in scopes:
        info["email"] = user.email
        info["email_verified"] = user.email_verified
    if "phone" in scopes:
        info["phone"] = user.phone
        info["phone_verified"] = user.phone_verified
    if "kyc_status" in scopes:
        info["kyc_tier"] = trust.kyc_tier
    if "trust_score" in scopes:
        info["trust_score"] = trust.trust_score
        info["risk_level"] = "low" if trust.trust_score >= 70 else ("medium" if trust.trust_score >= 40 else "high")
    return info


# ── Introspect endpoint ───────────────────────────────────────────────────────

async def introspect_token(db: AsyncSession, token: str, client_id: str, client_secret: str) -> dict:
    # Validate calling client
    app_result = await db.execute(select(RegisteredApp).where(RegisteredApp.client_id == client_id))
    app = app_result.scalar_one_or_none()
    if not app or not verify_password(client_secret, app.client_secret_hash):
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_aud": False})
    except JWTError:
        return {"active": False}

    if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
        return {"active": False}

    user_id = payload.get("sub")
    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user or not user.is_active:
        return {"active": False}

    trust = await trust_service.get_trust_profile(db, user)
    risk_level = "low" if trust.trust_score >= 70 else ("medium" if trust.trust_score >= 40 else "high")

    return {
        "active": True,
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "trust_score": trust.trust_score,
        "kyc_tier": trust.kyc_tier,
        "risk_level": risk_level,
        "scopes": payload.get("scope", "").split(),
        "exp": payload.get("exp"),
        "iss": payload.get("iss"),
        "client_id": payload.get("client_id"),
    }
