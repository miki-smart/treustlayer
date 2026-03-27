"""
Unit tests for App Registry module use cases.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.modules.app_registry.application.use_cases.register_app import RegisterAppUseCase
from app.modules.app_registry.application.use_cases.approve_app import ApproveAppUseCase
from app.modules.app_registry.application.use_cases.list_apps import ListAppsUseCase
from app.modules.app_registry.domain.entities.app import App
from app.modules.identity.domain.entities.user import User, UserRole
from app.core.exceptions import NotFoundError, BadRequestError


class TestRegisterAppUseCase:
    """Test RegisterAppUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "app_repo": AsyncMock(),
            "user_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return RegisterAppUseCase(
            app_repo=mock_repos["app_repo"],
            user_repo=mock_repos["user_repo"],
        )
    
    @pytest.fixture
    def test_user(self):
        """Create test user."""
        return User(
            id="user-123",
            email="owner@example.com",
            username="appowner",
            hashed_password="hashed",
            role=UserRole.APP_OWNER,
            is_active=True,
        )
    
    @pytest.mark.asyncio
    async def test_register_app_success(self, use_case, mock_repos, test_user):
        """Test successful app registration."""
        mock_repos["user_repo"].get_by_id.return_value = test_user
        mock_repos["app_repo"].create.return_value = App(
            name="Test App",
            owner_id=test_user.id,
            allowed_scopes=["openid", "profile"],
            redirect_uris=["http://localhost:3000/callback"],
            client_id="app_abc123",
            client_secret_hash="hash",
            api_key_hash="hash",
        )
        
        app, client_secret, api_key = await use_case.execute(
            owner_id=test_user.id,
            name="Test App",
            allowed_scopes=["openid", "profile"],
            redirect_uris=["http://localhost:3000/callback"],
            description="Test app description",
        )
        
        assert app.name == "Test App"
        assert app.owner_id == test_user.id
        assert len(client_secret) > 0
        assert len(api_key) > 0
        mock_repos["app_repo"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_app_owner_not_found(self, use_case, mock_repos):
        """Test app registration with non-existent owner."""
        mock_repos["user_repo"].get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="Owner not found"):
            await use_case.execute(
                owner_id="non-existent",
                name="Test App",
                allowed_scopes=["openid"],
                redirect_uris=["http://localhost:3000"],
            )
    
    @pytest.mark.asyncio
    async def test_register_app_empty_name(self, use_case, mock_repos, test_user):
        """Test app registration with empty name."""
        mock_repos["user_repo"].get_by_id.return_value = test_user
        
        with pytest.raises(BadRequestError, match="name is required"):
            await use_case.execute(
                owner_id=test_user.id,
                name="",
                allowed_scopes=["openid"],
                redirect_uris=["http://localhost:3000"],
            )
    
    @pytest.mark.asyncio
    async def test_register_app_no_scopes(self, use_case, mock_repos, test_user):
        """Test app registration without scopes."""
        mock_repos["user_repo"].get_by_id.return_value = test_user
        
        with pytest.raises(BadRequestError, match="At least one scope"):
            await use_case.execute(
                owner_id=test_user.id,
                name="Test App",
                allowed_scopes=[],
                redirect_uris=["http://localhost:3000"],
            )
    
    @pytest.mark.asyncio
    async def test_register_app_no_redirect_uris(self, use_case, mock_repos, test_user):
        """Test app registration without redirect URIs."""
        mock_repos["user_repo"].get_by_id.return_value = test_user
        
        with pytest.raises(BadRequestError, match="At least one redirect URI"):
            await use_case.execute(
                owner_id=test_user.id,
                name="Test App",
                allowed_scopes=["openid"],
                redirect_uris=[],
            )


class TestApproveAppUseCase:
    """Test ApproveAppUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return ApproveAppUseCase(app_repo=mock_repo)
    
    @pytest.fixture
    def test_app(self):
        """Create test app."""
        return App(
            id="app-123",
            name="Test App",
            owner_id="user-123",
            allowed_scopes=["openid"],
            redirect_uris=["http://localhost:3000"],
            client_id="app_abc",
            client_secret_hash="hash",
            api_key_hash="hash",
            is_approved=False,
        )
    
    @pytest.mark.asyncio
    async def test_approve_app_success(self, use_case, mock_repo, test_app):
        """Test successful app approval."""
        mock_repo.get_by_id.return_value = test_app
        mock_repo.update.return_value = test_app
        
        await use_case.execute(app_id="app-123")
        
        assert test_app.is_approved is True
        mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_app_not_found(self, use_case, mock_repo):
        """Test approving non-existent app."""
        mock_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="App not found"):
            await use_case.execute(app_id="non-existent")


class TestListAppsUseCase:
    """Test ListAppsUseCase."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repo):
        """Create use case instance."""
        return ListAppsUseCase(app_repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_list_all_apps(self, use_case, mock_repo):
        """Test listing all apps."""
        mock_apps = [
            App(
                name=f"App {i}",
                owner_id="user-123",
                allowed_scopes=["openid"],
                redirect_uris=["http://localhost:3000"],
                client_id=f"app_{i}",
                client_secret_hash="hash",
                api_key_hash="hash",
            )
            for i in range(5)
        ]
        mock_repo.list_all.return_value = mock_apps
        
        result = await use_case.list_all(skip=0, limit=50)
        
        assert len(result) == 5
        mock_repo.list_all.assert_called_once_with(0, 50)
    
    @pytest.mark.asyncio
    async def test_list_by_owner(self, use_case, mock_repo):
        """Test listing apps by owner."""
        mock_apps = [
            App(
                name=f"App {i}",
                owner_id="user-123",
                allowed_scopes=["openid"],
                redirect_uris=["http://localhost:3000"],
                client_id=f"app_{i}",
                client_secret_hash="hash",
                api_key_hash="hash",
            )
            for i in range(3)
        ]
        mock_repo.list_by_owner.return_value = mock_apps
        
        result = await use_case.list_by_owner(owner_id="user-123")
        
        assert len(result) == 3
        assert all(app.owner_id == "user-123" for app in result)
        mock_repo.list_by_owner.assert_called_once_with("user-123")
    
    @pytest.mark.asyncio
    async def test_list_marketplace(self, use_case, mock_repo):
        """Test listing marketplace apps."""
        mock_apps = [
            App(
                name=f"Public App {i}",
                owner_id="user-123",
                allowed_scopes=["openid"],
                redirect_uris=["http://localhost:3000"],
                client_id=f"app_{i}",
                client_secret_hash="hash",
                api_key_hash="hash",
                is_public=True,
                is_approved=True,
            )
            for i in range(2)
        ]
        mock_repo.list_public.return_value = mock_apps
        
        result = await use_case.list_marketplace(skip=0, limit=50)
        
        assert len(result) == 2
        assert all(app.is_public and app.is_approved for app in result)
        mock_repo.list_public.assert_called_once_with(0, 50)
