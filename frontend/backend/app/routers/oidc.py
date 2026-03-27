"""
OIDC / OAuth2 endpoints.

  GET  /oauth/authorize        — generate auth code (user must be logged in)
  POST /oauth/token            — exchange code or refresh token for tokens
  GET  /oauth/userinfo         — return user claims from access token
  POST /oauth/introspect       — validate token + return trust info for relying party
  GET  /oauth/.well-known/openid-configuration — OIDC discovery document
"""
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional

from app.dependencies import CurrentUser, DB
from app.services import oidc_service
from app.config import settings

router = APIRouter(prefix="/oauth", tags=["OIDC / Federation"])

SUPPORTED_SCOPES = ["openid", "profile", "email", "phone", "address", "kyc_status", "trust_score"]


# ── Discovery ────────────────────────────────────────────────────────────────

@router.get("/.well-known/openid-configuration", include_in_schema=False)
async def openid_configuration(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": oidc_service.ISSUER,
        "authorization_endpoint": f"{base}/api/v1/oauth/authorize",
        "token_endpoint": f"{base}/api/v1/oauth/token",
        "userinfo_endpoint": f"{base}/api/v1/oauth/userinfo",
        "introspection_endpoint": f"{base}/api/v1/oauth/introspect",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": SUPPORTED_SCOPES,
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "claims_supported": [
            "sub", "name", "email", "email_verified",
            "phone", "phone_verified", "picture",
            "kyc_tier", "trust_score",
        ],
    }


# ── Authorization Endpoint ───────────────────────────────────────────────────

@router.get("/authorize", summary="OIDC Authorization endpoint")
async def authorize(
    current_user: CurrentUser,
    db: DB,
    client_id: str = "",
    redirect_uri: str = "",
    scope: str = "openid profile email",
    response_type: str = "code",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256",
):
    """
    Start the Authorization Code flow.
    User must be authenticated (Bearer token from TrustLayer login).
    Returns JSON with the authorization code (in a real flow this would redirect).
    """
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Only response_type=code is supported")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=400, detail="client_id and redirect_uri are required")

    scopes = [s.strip() for s in scope.split() if s.strip() in SUPPORTED_SCOPES]
    if not scopes:
        raise HTTPException(status_code=400, detail="No valid scopes requested")

    code = await oidc_service.create_authorization_code(
        db=db,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scopes=scopes,
        user=current_user,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    # In a real OIDC flow, this would redirect to redirect_uri?code=...&state=...
    # Returning JSON for API-first usage
    return {
        "code": code,
        "state": state,
        "redirect_uri": f"{redirect_uri}?code={code}" + (f"&state={state}" if state else ""),
    }


# ── Token Endpoint ───────────────────────────────────────────────────────────

@router.post("/token", summary="OIDC Token endpoint")
async def token(
    db: DB,
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
):
    """
    Exchange an authorization code (or refresh token) for access/id/refresh tokens.
    Supports `authorization_code` and `refresh_token` grant types.
    """
    return await oidc_service.exchange_code_for_tokens(
        db=db,
        grant_type=grant_type,
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        refresh_token=refresh_token,
    )


# ── UserInfo Endpoint ────────────────────────────────────────────────────────

@router.get("/userinfo", summary="Return user claims from OIDC access token")
async def userinfo(request: Request, db: DB):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = auth_header[7:]
    return await oidc_service.get_userinfo(db, token)


# ── Introspect Endpoint ───────────────────────────────────────────────────────

@router.post("/introspect", summary="Validate token and return trust info (relying party)")
async def introspect(
    db: DB,
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    """
    Called by relying party apps to validate a user's access token.
    Returns token validity + trust score, KYC tier, and risk level.
    """
    return await oidc_service.introspect_token(db, token, client_id, client_secret)
