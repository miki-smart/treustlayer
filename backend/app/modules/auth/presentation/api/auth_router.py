from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.exceptions import ForbiddenError, UnauthorizedError, ValidationError
from app.core.security import create_access_token, decode_token
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService
from app.modules.app_registry.infrastructure.persistence.app_repository_impl import SQLAlchemyAppRepository
from app.modules.auth.application.dto.auth_dto import AuthorizeDTO, TokenRequestDTO
from app.modules.auth.application.use_cases.authorize import AuthorizeUseCase
from app.modules.auth.application.use_cases.exchange_token import ExchangeTokenUseCase
from app.modules.auth.application.use_cases.introspect import IntrospectUseCase
from app.modules.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from app.modules.auth.application.use_cases.userinfo import UserInfoUseCase
from app.modules.auth.infrastructure.persistence.auth_code_repository_impl import SQLAlchemyAuthCodeRepository
from app.modules.auth.presentation.schemas.auth_schemas import (
    AuthorizeRequest,
    AuthorizeResponse,
    IntrospectRequest,
    IntrospectResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    TokenRequest,
    TokenResponse,
    UserInfoResponse,
)
from app.modules.consent.application.services.consent_service import ConsentService
from app.modules.consent.infrastructure.persistence.consent_repository_impl import SQLAlchemyConsentRepository
from app.modules.identity.application.services.identity_service import IdentityService
from app.modules.identity.infrastructure.persistence.user_repository_impl import SQLAlchemyUserRepository
from app.modules.kyc.application.services.kyc_service import KYCService
from app.modules.kyc.infrastructure.persistence.kyc_repository_impl import SQLAlchemyKYCRepository
from app.modules.session.application.services.session_service import SessionService
from app.modules.session.infrastructure.persistence.refresh_token_repository_impl import SQLAlchemyRefreshTokenRepository

router = APIRouter(prefix="/auth", tags=["Auth / OIDC"])
bearer_scheme = HTTPBearer(auto_error=False)


# ── dependency factories ─────────────────────────────────────────────────────

def _make_identity(session: AsyncSession) -> IdentityService:
    return IdentityService(SQLAlchemyUserRepository(session))


def _make_kyc(session: AsyncSession) -> KYCService:
    return KYCService(SQLAlchemyKYCRepository(session))


def _make_registry(session: AsyncSession) -> AppRegistryService:
    return AppRegistryService(SQLAlchemyAppRepository(session))


def _make_consent(session: AsyncSession) -> ConsentService:
    return ConsentService(SQLAlchemyConsentRepository(session))


def _make_session_svc(session: AsyncSession) -> SessionService:
    return SessionService(SQLAlchemyRefreshTokenRepository(session))


# ── endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/authorize",
    response_model=AuthorizeResponse,
    summary="OIDC Authorization — authenticate user and issue an auth code",
)
async def authorize(
    payload: AuthorizeRequest,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = AuthorizeUseCase(
        code_repository=SQLAlchemyAuthCodeRepository(session),
        identity_service=_make_identity(session),
        app_registry_service=_make_registry(session),
        consent_service=_make_consent(session),
    )
    try:
        result = await use_case.execute(
            AuthorizeDTO(
                username=payload.username,
                password=payload.password,
                client_id=payload.client_id,
                redirect_uri=payload.redirect_uri,
                scope=payload.scope,
                state=payload.state,
                code_challenge=payload.code_challenge,
                code_challenge_method=payload.code_challenge_method,
            )
        )
        await session.commit()
        return AuthorizeResponse(
            code=result.code,
            state=result.state,
            redirect_uri=result.redirect_uri,
        )
    except (ValidationError, ForbiddenError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Token endpoint — exchange auth code or refresh token",
)
async def token(
    payload: TokenRequest,
    session: AsyncSession = Depends(get_async_session),
):
    dto = TokenRequestDTO(
        grant_type=payload.grant_type,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        code=payload.code,
        redirect_uri=payload.redirect_uri,
        code_verifier=payload.code_verifier,
        refresh_token=payload.refresh_token,
    )
    try:
        if payload.grant_type == "authorization_code":
            use_case = ExchangeTokenUseCase(
                code_repository=SQLAlchemyAuthCodeRepository(session),
                identity_service=_make_identity(session),
                kyc_service=_make_kyc(session),
                app_registry_service=_make_registry(session),
                session_service=_make_session_svc(session),
            )
        else:
            use_case = RefreshTokenUseCase(  # type: ignore[assignment]
                identity_service=_make_identity(session),
                kyc_service=_make_kyc(session),
                app_registry_service=_make_registry(session),
                session_service=_make_session_svc(session),
            )

        result = await use_case.execute(dto)
        await session.commit()
        return TokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            expires_in=result.expires_in,
            scope=result.scope,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except UnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get(
    "/userinfo",
    response_model=UserInfoResponse,
    summary="OIDC UserInfo — return user claims from access token",
)
async def userinfo(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    use_case = UserInfoUseCase(
        identity_service=_make_identity(session),
        kyc_service=_make_kyc(session),
    )
    try:
        result = await use_case.execute(credentials.credentials)
        return UserInfoResponse(
            sub=result.sub,
            username=result.username,
            email=result.email,
            full_name=result.full_name,
            email_verified=result.email_verified,
            kyc_tier=result.kyc_tier,
            trust_score=result.trust_score,
        )
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/introspect",
    response_model=IntrospectResponse,
    summary="RFC 7662 Token Introspection — high-risk validation endpoint",
)
async def introspect(
    payload: IntrospectRequest,
    session: AsyncSession = Depends(get_async_session),
):
    use_case = IntrospectUseCase(
        app_registry_service=_make_registry(session),
        kyc_service=_make_kyc(session),
    )
    result = await use_case.execute(
        token=payload.token,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
    )
    return IntrospectResponse(**result.__dict__)


# ── Frontend-specific endpoints ──────────────────────────────────────────────

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Direct user login — returns JWT for frontend sessions",
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Simple email/password login for frontend users.
    Returns a short-lived JWT and an optional refresh token.
    No OIDC client required — this is the browser session entry point.
    """
    identity_svc = _make_identity(session)
    user = await identity_svc.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or account inactive",
        )

    kyc_svc = _make_kyc(session)
    kyc_status = await kyc_svc.get_kyc_status(user.id)
    kyc_tier = kyc_status.tier if kyc_status else "tier_0"
    trust_score = kyc_status.trust_score if kyc_status else 0

    access_token = create_access_token(
        subject=user.id,
        extra_claims={
            "username": user.username,
            "role": user.role.value,
            "kyc_tier": kyc_tier,
            "trust_score": trust_score,
        },
    )

    # Issue a refresh token for frontend sessions
    session_svc = _make_session_svc(session)
    raw_refresh = await session_svc.create_refresh_token(
        user_id=user.id,
        client_id="__frontend__",
        scopes=["openid"],
    )
    await session.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — revoke the refresh token",
)
async def logout(
    payload: LogoutRequest,
    session: AsyncSession = Depends(get_async_session),
):
    session_svc = _make_session_svc(session)
    await session_svc.revoke_refresh_token(payload.refresh_token)
    await session.commit()

