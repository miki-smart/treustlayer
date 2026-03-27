"""
AuthorizeUseCase — handles the /authorize flow.

Steps:
  1. Validate client registration (app_registry_service)
  2. Validate redirect_uri is registered
  3. Validate requested scopes are allowed for this client
  4. Authenticate user credentials (identity_service)
  5. Ensure consent exists; auto-grant if not (consent_service)
  6. Create a short-lived authorization code with optional PKCE
  7. Return the code for redirect
"""
from app.core.exceptions import ForbiddenError, UnauthorizedError, ValidationError
from app.modules.auth.application.dto.auth_dto import AuthorizeDTO, AuthorizeResultDTO
from app.modules.auth.domain.entities.authorization_code import AuthorizationCode
from app.modules.auth.domain.repositories.auth_code_repository import AuthCodeRepository
from app.modules.app_registry.application.services.app_registry_service import AppRegistryService
from app.modules.consent.application.services.consent_service import ConsentService
from app.modules.identity.application.services.identity_service import IdentityService


class AuthorizeUseCase:
    def __init__(
        self,
        code_repository: AuthCodeRepository,
        identity_service: IdentityService,
        app_registry_service: AppRegistryService,
        consent_service: ConsentService,
    ) -> None:
        self._codes = code_repository
        self._identity = identity_service
        self._registry = app_registry_service
        self._consent = consent_service

    async def execute(self, dto: AuthorizeDTO) -> AuthorizeResultDTO:
        # 1 — validate client (no secret required at /authorize)
        app = await self._registry.get_app_by_client_id(dto.client_id)
        if not app or not app.is_active or not app.is_approved:
            raise ValidationError("Unknown or unapproved client")

        # 2 — validate redirect_uri
        if not app.has_redirect_uri(dto.redirect_uri):
            raise ValidationError("redirect_uri is not registered for this client")

        # 3 — validate scopes
        requested_scopes = dto.scopes_list()
        if not requested_scopes:
            raise ValidationError("At least one scope is required")
        if not app.validate_scopes(requested_scopes):
            raise ForbiddenError("Requested scopes exceed client permissions")

        # 4 — authenticate user
        user = await self._identity.authenticate_user(dto.username, dto.password)
        if not user:
            raise UnauthorizedError("Invalid credentials")

        # 5 — ensure consent
        has = await self._consent.has_consent(user.id, dto.client_id, requested_scopes)
        if not has:
            # Auto-grant consent on first authorize (production would show consent UI)
            await self._consent.grant_consent(user.id, dto.client_id, requested_scopes)

        # 6 — create authorization code
        auth_code = AuthorizationCode(
            client_id=dto.client_id,
            user_id=user.id,
            redirect_uri=dto.redirect_uri,
            scopes=requested_scopes,
            code_challenge=dto.code_challenge,
            code_challenge_method=dto.code_challenge_method,
        )
        auth_code = await self._codes.create(auth_code)

        return AuthorizeResultDTO(
            code=auth_code.code,
            state=dto.state,
            redirect_uri=dto.redirect_uri,
        )
