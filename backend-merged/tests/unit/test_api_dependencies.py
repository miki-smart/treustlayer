"""
Unit tests for API dependencies and middleware.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.api.dependencies import (
    get_current_user,
    get_current_active_user,
    require_roles,
)
from app.modules.identity.domain.entities.user import User, UserRole
from app.core.exceptions import UnauthorizedError, ForbiddenError


class TestGetCurrentUser:
    """Test get_current_user dependency."""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Create mock user repository."""
        return AsyncMock()
    
    @pytest.fixture
    def test_user(self):
        """Create test user."""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_user_repo, test_user):
        """Test getting current user with valid token."""
        from unittest.mock import patch
        
        mock_user_repo.get_by_id.return_value = test_user
        
        with patch("app.core.security.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": test_user.id}
            
            dependency = get_current_user(user_repo=mock_user_repo)
            result = await dependency(token="valid-token")
            
            assert result.id == test_user.id
            mock_user_repo.get_by_id.assert_called_once_with(test_user.id)
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_user_repo):
        """Test getting current user with invalid token."""
        from unittest.mock import patch
        from jose import JWTError
        
        with patch("app.core.security.decode_token") as mock_decode:
            mock_decode.side_effect = JWTError("Invalid token")
            
            dependency = get_current_user(user_repo=mock_user_repo)
            
            with pytest.raises(UnauthorizedError):
                await dependency(token="invalid-token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_user_repo):
        """Test getting current user when user doesn't exist."""
        from unittest.mock import patch
        
        mock_user_repo.get_by_id.return_value = None
        
        with patch("app.core.security.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "non-existent"}
            
            dependency = get_current_user(user_repo=mock_user_repo)
            
            with pytest.raises(UnauthorizedError, match="User not found"):
                await dependency(token="valid-token")


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""
    
    @pytest.fixture
    def active_user(self):
        """Create active user."""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
    
    @pytest.fixture
    def inactive_user(self):
        """Create inactive user."""
        return User(
            id="user-456",
            email="inactive@example.com",
            username="inactive",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=False,
        )
    
    def test_get_current_active_user_success(self, active_user):
        """Test getting active user."""
        dependency = get_current_active_user
        result = dependency(current_user=active_user)
        
        assert result == active_user
    
    def test_get_current_active_user_inactive(self, inactive_user):
        """Test getting inactive user raises error."""
        dependency = get_current_active_user
        
        with pytest.raises(UnauthorizedError, match="deactivated"):
            dependency(current_user=inactive_user)


class TestRequireRoles:
    """Test require_roles dependency."""
    
    @pytest.fixture
    def user(self):
        """Create regular user."""
        return User(
            id="user-123",
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
    
    @pytest.fixture
    def admin(self):
        """Create admin user."""
        return User(
            id="admin-123",
            email="admin@example.com",
            username="admin",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
    
    @pytest.fixture
    def kyc_approver(self):
        """Create KYC approver."""
        return User(
            id="kyc-123",
            email="kyc@example.com",
            username="kyc",
            hashed_password="hashed",
            role=UserRole.KYC_APPROVER,
            is_active=True,
        )
    
    def test_require_roles_single_role_allowed(self, user):
        """Test single role requirement - allowed."""
        dependency = require_roles([UserRole.USER])
        result = dependency(current_user=user)
        
        assert result == user
    
    def test_require_roles_single_role_denied(self, user):
        """Test single role requirement - denied."""
        dependency = require_roles([UserRole.ADMIN])
        
        with pytest.raises(ForbiddenError):
            dependency(current_user=user)
    
    def test_require_roles_multiple_roles_allowed(self, kyc_approver):
        """Test multiple role requirement - allowed."""
        dependency = require_roles([UserRole.ADMIN, UserRole.KYC_APPROVER])
        result = dependency(current_user=kyc_approver)
        
        assert result == kyc_approver
    
    def test_require_roles_admin_access(self, admin):
        """Test admin can access admin-only endpoints."""
        dependency = require_roles([UserRole.ADMIN])
        result = dependency(current_user=admin)
        
        assert result == admin
    
    def test_require_roles_user_cannot_access_admin(self, user):
        """Test regular user cannot access admin endpoints."""
        dependency = require_roles([UserRole.ADMIN])
        
        with pytest.raises(ForbiddenError, match="Insufficient permissions"):
            dependency(current_user=user)
    
    def test_require_roles_empty_list(self, user):
        """Test empty role list allows any authenticated user."""
        dependency = require_roles([])
        result = dependency(current_user=user)
        
        assert result == user
