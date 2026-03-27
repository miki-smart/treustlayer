import secrets

from app.core.events import event_bus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import hash_secret
from app.modules.app_registry.application.dto.app_dto import AppResponseDTO, RegisterAppDTO
from app.modules.app_registry.domain.entities.app import RegisteredApp
from app.modules.app_registry.domain.events.app_events import AppApprovedEvent, AppRegisteredEvent
from app.modules.app_registry.domain.repositories.app_repository import AppRepository
from app.modules.identity.domain.entities.user import UserRole


class RegisterAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, dto: RegisterAppDTO) -> AppResponseDTO:
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(40)
        api_key = f"tl_{secrets.token_urlsafe(32)}"

        app = RegisteredApp(
            name=dto.name,
            client_id=client_id,
            client_secret_hash=hash_secret(client_secret),
            api_key_hash=hash_secret(api_key),
            owner_id=dto.owner_id,
            allowed_scopes=dto.allowed_scopes,
            redirect_uris=dto.redirect_uris,
            description=dto.description,
        )
        app = await self._repo.create(app)

        await event_bus.publish(
            AppRegisteredEvent(app_id=app.id, client_id=app.client_id, name=app.name)
        )

        return AppResponseDTO(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            client_secret=client_secret,  # only returned now — never again
            api_key=api_key,              # only returned now — never again
            owner_id=app.owner_id,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            is_active=app.is_active,
            is_approved=app.is_approved,
        )


class ApproveAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str) -> AppResponseDTO:
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App", app_id)

        app.approve()
        app = await self._repo.update(app)

        await event_bus.publish(AppApprovedEvent(app_id=app.id, client_id=app.client_id))

        return _to_dto(app)


def _to_dto(app: RegisteredApp) -> AppResponseDTO:
    return AppResponseDTO(
        id=app.id,
        name=app.name,
        client_id=app.client_id,
        owner_id=app.owner_id,
        allowed_scopes=app.allowed_scopes,
        redirect_uris=app.redirect_uris,
        description=app.description,
        is_active=app.is_active,
        is_approved=app.is_approved,
    )


def _assert_owner_or_admin(app: RegisteredApp, caller_id: str, caller_role: str) -> None:
    """Raise ForbiddenError unless the caller owns the app or is an ADMIN."""
    if caller_role == UserRole.ADMIN:
        return
    if app.owner_id != caller_id:
        raise ForbiddenError("You do not have permission to modify this application")


class UpdateAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(
        self,
        app_id: str,
        caller_id: str,
        caller_role: str,
        name: str | None = None,
        description: str | None = None,
        allowed_scopes: list[str] | None = None,
        redirect_uris: list[str] | None = None,
    ) -> AppResponseDTO:
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App", app_id)
        _assert_owner_or_admin(app, caller_id, caller_role)
        app.update_config(
            name=name,
            description=description,
            allowed_scopes=allowed_scopes,
            redirect_uris=redirect_uris,
        )
        app = await self._repo.update(app)
        return _to_dto(app)


class RotateApiKeyUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str, caller_id: str, caller_role: str) -> AppResponseDTO:
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App", app_id)
        _assert_owner_or_admin(app, caller_id, caller_role)
        new_api_key = f"tl_{secrets.token_urlsafe(32)}"
        app.api_key_hash = hash_secret(new_api_key)
        app = await self._repo.update(app)
        dto = _to_dto(app)
        dto.api_key = new_api_key  # returned once only
        return dto


class RotateClientSecretUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str, caller_id: str, caller_role: str) -> AppResponseDTO:
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App", app_id)
        _assert_owner_or_admin(app, caller_id, caller_role)
        new_secret = secrets.token_urlsafe(40)
        app.client_secret_hash = hash_secret(new_secret)
        app = await self._repo.update(app)
        dto = _to_dto(app)
        dto.client_secret = new_secret  # returned once only
        return dto


class DeactivateAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str) -> AppResponseDTO:
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App", app_id)
        app.deactivate()
        app = await self._repo.update(app)
        return _to_dto(app)


class ListOwnAppsUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(
        self, owner_id: str, skip: int = 0, limit: int = 50
    ) -> list[AppResponseDTO]:
        apps = await self._repo.get_by_owner_id(owner_id, skip=skip, limit=limit)
        return [_to_dto(a) for a in apps]


class RegisterAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, dto: RegisterAppDTO) -> AppResponseDTO:
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(40)
        api_key = f"tl_{secrets.token_urlsafe(32)}"

        app = RegisteredApp(
            name=dto.name,
            client_id=client_id,
            client_secret_hash=hash_secret(client_secret),
            api_key_hash=hash_secret(api_key),
            allowed_scopes=dto.allowed_scopes,
            redirect_uris=dto.redirect_uris,
            description=dto.description,
        )
        app = await self._repo.create(app)

        await event_bus.publish(
            AppRegisteredEvent(app_id=app.id, client_id=app.client_id, name=app.name)
        )

        return AppResponseDTO(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            client_secret=client_secret,  # only returned now — never again
            api_key=api_key,              # only returned now — never again
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            is_active=app.is_active,
            is_approved=app.is_approved,
        )


class ApproveAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str) -> AppResponseDTO:
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NotFoundError("App", app_id)

        app.approve()
        app = await self._repo.update(app)

        await event_bus.publish(AppApprovedEvent(app_id=app.id, client_id=app.client_id))

        return AppResponseDTO(
            id=app.id,
            name=app.name,
            client_id=app.client_id,
            allowed_scopes=app.allowed_scopes,
            redirect_uris=app.redirect_uris,
            description=app.description,
            is_active=app.is_active,
            is_approved=app.is_approved,
        )


def _to_dto(app: "RegisteredApp") -> AppResponseDTO:
    return AppResponseDTO(
        id=app.id,
        name=app.name,
        client_id=app.client_id,
        allowed_scopes=app.allowed_scopes,
        redirect_uris=app.redirect_uris,
        description=app.description,
        is_active=app.is_active,
        is_approved=app.is_approved,
    )


class UpdateAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(
        self,
        app_id: str,
        name: str | None = None,
        description: str | None = None,
        allowed_scopes: list[str] | None = None,
        redirect_uris: list[str] | None = None,
    ) -> AppResponseDTO:
        from app.core.exceptions import NotFoundError as NFE
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NFE("App", app_id)
        app.update_config(
            name=name,
            description=description,
            allowed_scopes=allowed_scopes,
            redirect_uris=redirect_uris,
        )
        app = await self._repo.update(app)
        return _to_dto(app)


class RotateApiKeyUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str) -> AppResponseDTO:
        from app.core.exceptions import NotFoundError as NFE
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NFE("App", app_id)
        new_api_key = f"tl_{secrets.token_urlsafe(32)}"
        app.api_key_hash = hash_secret(new_api_key)
        app = await self._repo.update(app)
        dto = _to_dto(app)
        dto.api_key = new_api_key  # returned once only
        return dto


class RotateClientSecretUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str) -> AppResponseDTO:
        from app.core.exceptions import NotFoundError as NFE
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NFE("App", app_id)
        new_secret = secrets.token_urlsafe(40)
        app.client_secret_hash = hash_secret(new_secret)
        app = await self._repo.update(app)
        dto = _to_dto(app)
        dto.client_secret = new_secret  # returned once only
        return dto


class DeactivateAppUseCase:
    def __init__(self, app_repository: AppRepository) -> None:
        self._repo = app_repository

    async def execute(self, app_id: str) -> AppResponseDTO:
        from app.core.exceptions import NotFoundError as NFE
        app = await self._repo.get_by_id(app_id)
        if not app:
            raise NFE("App", app_id)
        app.deactivate()
        app = await self._repo.update(app)
        return _to_dto(app)
