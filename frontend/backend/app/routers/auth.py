"""
Auth / OIDC endpoints — /api/v1/auth/*

  POST /auth/login       — direct frontend login
  POST /auth/logout      — revoke refresh token
  POST /auth/authorize   — OIDC auth code issuance (credentials inline)
  POST /auth/token       — exchange code/refresh for tokens
  GET  /auth/userinfo    — OIDC user claims
  POST /auth/introspect  — RFC 7662 token introspection

Legacy routes (kept for backward compat):
  GET  /auth/me
  POST /auth/refresh
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, DB
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse, UserOut, UserUpdate
from app.services import auth_service, oidc_service, trust_service

router = APIRouter(prefix="/auth", tags=["Auth / OIDC"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    username: str
    role: str


class LogoutRequest(BaseModel):
    """POST /auth/logout — revoke the refresh token."""
    refresh_token: str


class AuthorizeRequest(BaseModel):
    """POST /auth/authorize — submit credentials + OAuth2 params."""
    username: str
    password: str
    client_id: str
    redirect_uri: str
    scope: str
    state: str | None = None
    code_challenge: str | None = None
    code_challenge_method: str | None = "S256"


class AuthorizeResponse(BaseModel):
    code: str
    state: str | None = None
    redirect_uri: str


class TokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    code: str | None = None
    redirect_uri: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None


class IntrospectRequest(BaseModel):
    token: str
    client_id: str
    client_secret: str


class UserInfoResponse(BaseModel):
    sub: str
    username: str
    email: str
    full_name: str | None = None
    email_verified: bool
    kyc_tier: str
    trust_score: int
    role: str | None = None


# ── Direct login (frontend session) ──────────────────────────────────────────

@router.post("/login", response_model=LoginResponse, summary="Direct user login — returns JWT for frontend sessions")
async def login(body: LoginRequest, db: DB):
    """Accepts email or username in the `email` field."""
    user = await auth_service.authenticate_user(db, body.email, body.password)
    access_token, refresh_token = await auth_service.create_tokens(db, user)
    from app.config import settings
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        username=user.username or user.email.split("@")[0],
        role=user.role,
    )


@router.post("/logout", status_code=204, summary="Logout — revoke the refresh token")
async def logout(body: LogoutRequest, db: DB):
    await auth_service.revoke_refresh_token(db, body.refresh_token)


# ── OIDC Authorization Code Flow ──────────────────────────────────────────────

@router.post("/authorize", response_model=AuthorizeResponse, summary="OIDC Authorization — authenticate user and issue an auth code")
async def authorize(body: AuthorizeRequest, db: DB):
    # Authenticate user with username or email
    user = await auth_service.authenticate_user(db, body.username, body.password)
    scopes = [s.strip() for s in body.scope.split() if s.strip()]
    code = await oidc_service.create_authorization_code(
        db=db,
        client_id=body.client_id,
        redirect_uri=body.redirect_uri,
        scopes=scopes,
        user=user,
        code_challenge=body.code_challenge,
        code_challenge_method=body.code_challenge_method,
    )
    return AuthorizeResponse(
        code=code,
        state=body.state,
        redirect_uri=f"{body.redirect_uri}?code={code}" + (f"&state={body.state}" if body.state else ""),
    )


@router.post("/token", summary="Token endpoint — exchange auth code or refresh token")
async def token(body: TokenRequest, db: DB):
    return await oidc_service.exchange_code_for_tokens(
        db=db,
        grant_type=body.grant_type,
        client_id=body.client_id,
        client_secret=body.client_secret,
        code=body.code,
        redirect_uri=body.redirect_uri,
        code_verifier=body.code_verifier,
        refresh_token=body.refresh_token,
    )


@router.get("/userinfo", response_model=UserInfoResponse, summary="OIDC UserInfo — return user claims from access token")
async def userinfo(request: Request, db: DB):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    claims = await oidc_service.get_userinfo(db, auth[7:])
    trust = None
    try:
        from sqlalchemy import select as sa_select
        from app.models.user import User as UserModel
        import uuid
        uid = uuid.UUID(claims["sub"])
        user_r = await db.execute(sa_select(UserModel).where(UserModel.id == uid))
        user = user_r.scalar_one_or_none()
        if user:
            trust = await trust_service.get_trust_profile(db, user)
    except Exception:
        pass
    return UserInfoResponse(
        sub=claims.get("sub", ""),
        username=claims.get("name", "").split(" ")[0] if claims.get("name") else "",
        email=claims.get("email", ""),
        full_name=claims.get("name"),
        email_verified=claims.get("email_verified", False),
        kyc_tier=f"tier_{trust.kyc_tier}" if trust else "tier_0",
        trust_score=int(trust.trust_score) if trust else 0,
        role=None,
    )


@router.post("/introspect", summary="RFC 7662 Token Introspection — high-risk validation endpoint")
async def introspect(body: IntrospectRequest, db: DB):
    result = await oidc_service.introspect_token(db, body.token, body.client_id, body.client_secret)
    if result.get("active"):
        result["username"] = result.pop("email", "")
        result["risk_flag"] = result.get("risk_level") == "high"
        result["kyc_tier"] = f"tier_{result.pop('kyc_tier', 0)}"
        result["trust_score"] = int(result.get("trust_score", 0))
    return result


# ── Legacy/backward compat ────────────────────────────────────────────────────

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(body: RefreshRequest, db: DB):
    access_token = await auth_service.refresh_access_token(db, body.refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser):
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(body: UserUpdate, current_user: CurrentUser):
    if body.name:
        current_user.name = body.name
    if body.avatar is not None:
        current_user.avatar = body.avatar
    if body.phone is not None:
        current_user.phone = body.phone
    return UserOut.model_validate(current_user)
