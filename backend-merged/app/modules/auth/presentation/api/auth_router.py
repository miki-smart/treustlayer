"""
Auth router � handles login, logout, and OIDC flows.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.dependencies import DBSession, CurrentUserId
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, hash_password, hash_secret, verify_password
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.auth.infrastructure.persistence.auth_repository_impl import SQLAlchemyAuthRepository
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.trust.infrastructure.persistence.trust_repository_impl import SQLAlchemyTrustRepository
from app.modules.biometric.infrastructure.persistence.biometric_repository_impl import SQLAlchemyBiometricRepository
from app.modules.digital_identity.infrastructure.persistence.identity_repository_impl import SQLAlchemyDigitalIdentityRepository
from app.modules.auth.application.use_cases.authorize import AuthorizeUseCase
from app.modules.auth.application.use_cases.exchange_token import ExchangeTokenUseCase
from app.modules.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from app.modules.auth.application.use_cases.introspect_token import IntrospectTokenUseCase
from app.modules.auth.application.use_cases.get_userinfo import GetUserInfoUseCase

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, session: DBSession):
    """Direct login for frontend."""
    repo = SQLAlchemyUserRepository(session)
    user_entity = await repo.get_by_email(payload.email.lower())
    
    if not user_entity or not verify_password(payload.password, user_entity.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user_entity.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    
    access_token = create_access_token(
        subject=user_entity.id,
        extra_claims={
            "username": user_entity.username,
            "role": user_entity.role.value,
            "email": user_entity.email,
        }
    )
    
    await session.commit()
    
    return LoginResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=900,
        user_id=user_entity.id,
        username=user_entity.username,
        role=user_entity.role.value,
    )


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: LogoutRequest, session: DBSession, current_user_id: CurrentUserId):
    """Logout (revoke refresh token if provided)."""
    if payload.refresh_token:
        auth_repo = SQLAlchemyAuthRepository(session)
        token_hash = hash_secret(payload.refresh_token)
        token = await auth_repo.get_refresh_token(token_hash)
        if token:
            await auth_repo.revoke_refresh_token(token.id)
    
    await session.commit()
    return None


# ============================================================================
# OIDC Endpoints
# ============================================================================

class AuthorizeRequest(BaseModel):
    email: str
    password: str
    client_id: str
    redirect_uri: str
    scopes: List[str]
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = "S256"


class AuthorizeResponse(BaseModel):
    code: str
    state: Optional[str]
    redirect_uri: str


@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize(payload: AuthorizeRequest, session: DBSession):
    """
    OIDC Authorization Endpoint.
    
    Step 1 of Authorization Code Flow:
    - Validates user credentials
    - Issues authorization code
    - Supports PKCE (code_challenge)
    """
    auth_repo = SQLAlchemyAuthRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    
    use_case = AuthorizeUseCase(auth_repo, user_repo)
    
    code = await use_case.execute(
        email=payload.email,
        password=payload.password,
        client_id=payload.client_id,
        redirect_uri=payload.redirect_uri,
        scopes=payload.scopes,
        state=payload.state,
        code_challenge=payload.code_challenge,
        code_challenge_method=payload.code_challenge_method,
    )
    
    await session.commit()
    
    return AuthorizeResponse(
        code=code.code,
        state=payload.state,
        redirect_uri=f"{code.redirect_uri}?code={code.code}&state={payload.state or ''}",
    )


class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    token_type: str
    expires_in: int


@router.post("/token", response_model=TokenResponse)
async def token(payload: TokenRequest, request: Request, session: DBSession):
    """
    OIDC Token Endpoint.
    
    Step 2 of Authorization Code Flow:
    - Exchanges authorization code for tokens
    - Verifies PKCE (code_verifier)
    - Issues access_token, refresh_token, id_token
    
    Also supports refresh_token grant type.
    """
    auth_repo = SQLAlchemyAuthRepository(session)
    user_repo = SQLAlchemyUserRepository(session)
    kyc_repo = SQLAlchemyKYCRepository(session)
    trust_repo = SQLAlchemyTrustRepository(session)
    biometric_repo = SQLAlchemyBiometricRepository(session)
    identity_repo = SQLAlchemyDigitalIdentityRepository(session)
    
    if payload.grant_type == "authorization_code":
        if not payload.code or not payload.redirect_uri:
            raise HTTPException(
                status_code=400, detail="code and redirect_uri required for authorization_code grant"
            )
        
        use_case = ExchangeTokenUseCase(
            auth_repo, user_repo, kyc_repo, trust_repo, biometric_repo, identity_repo
        )
        
        device_info = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        
        tokens = await use_case.execute(
            code=payload.code,
            client_id=payload.client_id,
            client_secret=payload.client_secret,
            redirect_uri=payload.redirect_uri,
            code_verifier=payload.code_verifier,
            device_info=device_info,
            ip_address=ip_address,
        )
        
        await session.commit()
        
        return TokenResponse(**tokens)
    
    elif payload.grant_type == "refresh_token":
        if not payload.refresh_token:
            raise HTTPException(status_code=400, detail="refresh_token required for refresh_token grant")
        
        use_case = RefreshTokenUseCase(
            auth_repo, user_repo, kyc_repo, trust_repo, biometric_repo, identity_repo
        )
        
        tokens = await use_case.execute(
            refresh_token_value=payload.refresh_token,
            client_id=payload.client_id,
            client_secret=payload.client_secret,
        )
        
        await session.commit()
        
        return TokenResponse(**tokens)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {payload.grant_type}")


@router.get("/userinfo")
async def userinfo(current_user_id: CurrentUserId, session: DBSession):
    """
    OIDC UserInfo Endpoint.
    
    Returns user claims based on granted scopes.
    Requires valid Bearer token.
    """
    user_repo = SQLAlchemyUserRepository(session)
    kyc_repo = SQLAlchemyKYCRepository(session)
    trust_repo = SQLAlchemyTrustRepository(session)
    biometric_repo = SQLAlchemyBiometricRepository(session)
    identity_repo = SQLAlchemyDigitalIdentityRepository(session)
    
    use_case = GetUserInfoUseCase(
        user_repo, kyc_repo, trust_repo, biometric_repo, identity_repo
    )
    
    claims = await use_case.execute(current_user_id)
    
    return claims


class IntrospectRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = "access_token"


@router.post("/introspect")
async def introspect(payload: IntrospectRequest):
    """
    Token Introspection Endpoint (RFC 7662).
    
    Allows resource servers to validate tokens.
    Returns active status and token claims.
    """
    use_case = IntrospectTokenUseCase()
    result = await use_case.execute(payload.token)
    return result


@router.get("/.well-known/openid-configuration")
async def discovery():
    """
    OIDC Discovery Document.
    
    Provides metadata about the OIDC provider.
    """
    return {
        "issuer": settings.ISSUER,
        "authorization_endpoint": f"{settings.ISSUER}/api/v1/auth/authorize",
        "token_endpoint": f"{settings.ISSUER}/api/v1/auth/token",
        "userinfo_endpoint": f"{settings.ISSUER}/api/v1/auth/userinfo",
        "jwks_uri": f"{settings.ISSUER}/api/v1/auth/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "scopes_supported": [
            "openid",
            "profile",
            "email",
            "phone",
            "kyc_status",
            "trust_score",
            "biometric",
            "identity",
        ],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "claims_supported": [
            "sub",
            "email",
            "email_verified",
            "name",
            "preferred_username",
            "phone_number",
            "phone_number_verified",
            "kyc_tier",
            "trust_score",
            "risk_level",
            "biometric_verified",
            "face_verified",
            "voice_verified",
            "digital_identity_id",
            "identity_status",
        ],
    }


@router.get("/.well-known/jwks.json")
async def jwks():
    """
    JSON Web Key Set (JWKS).
    
    Provides public keys for JWT signature verification.
    """
    import base64
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    
    try:
        public_key_pem = settings.JWT_PUBLIC_KEY.encode()
        public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
        
        public_numbers = public_key.public_numbers()
        
        n_bytes = public_numbers.n.to_bytes(
            (public_numbers.n.bit_length() + 7) // 8, byteorder="big"
        )
        e_bytes = public_numbers.e.to_bytes(
            (public_numbers.e.bit_length() + 7) // 8, byteorder="big"
        )
        
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "trustlayer-2026",
                    "alg": "RS256",
                    "n": base64.urlsafe_b64encode(n_bytes).decode().rstrip("="),
                    "e": base64.urlsafe_b64encode(e_bytes).decode().rstrip("="),
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate JWKS: {str(e)}")
