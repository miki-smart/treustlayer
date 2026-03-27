"""
Unit tests for RBAC (Role-Based Access Control).
"""
import pytest
from unittest.mock import MagicMock

from app.modules.identity.domain.entities.user import User, UserRole
from app.api.dependencies import require_roles


class TestRBAC:
    """Test RBAC functionality."""
    
    def test_user_role_hierarchy(self):
        """Test user role definitions."""
        assert UserRole.USER.value == "user"
        assert UserRole.APP_OWNER.value == "app_owner"
        assert UserRole.KYC_APPROVER.value == "kyc_approver"
        assert UserRole.ADMIN.value == "admin"
    
    def test_require_roles_user_allowed(self):
        """Test require_roles allows correct role."""
        user = User(
            id="user-123",
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
        
        dependency = require_roles([UserRole.USER])
        result = dependency(current_user=user)
        
        assert result == user
    
    def test_require_roles_admin_allowed(self):
        """Test require_roles allows admin."""
        admin = User(
            id="admin-123",
            email="admin@example.com",
            username="admin",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True,
        )
        
        dependency = require_roles([UserRole.ADMIN])
        result = dependency(current_user=admin)
        
        assert result == admin
    
    def test_require_roles_multiple_allowed(self):
        """Test require_roles with multiple allowed roles."""
        kyc_approver = User(
            id="kyc-123",
            email="kyc@example.com",
            username="kyc",
            hashed_password="hashed",
            role=UserRole.KYC_APPROVER,
            is_active=True,
        )
        
        dependency = require_roles([UserRole.ADMIN, UserRole.KYC_APPROVER])
        result = dependency(current_user=kyc_approver)
        
        assert result == kyc_approver
    
    def test_require_roles_forbidden(self):
        """Test require_roles denies incorrect role."""
        from app.core.exceptions import ForbiddenError
        
        user = User(
            id="user-123",
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
        
        dependency = require_roles([UserRole.ADMIN])
        
        with pytest.raises(ForbiddenError):
            dependency(current_user=user)
    
    def test_app_owner_cannot_access_kyc_queue(self):
        """Test app owner cannot access KYC queue."""
        from app.core.exceptions import ForbiddenError
        
        app_owner = User(
            id="owner-123",
            email="owner@example.com",
            username="owner",
            hashed_password="hashed",
            role=UserRole.APP_OWNER,
            is_active=True,
        )
        
        dependency = require_roles([UserRole.ADMIN, UserRole.KYC_APPROVER])
        
        with pytest.raises(ForbiddenError):
            dependency(current_user=app_owner)
    
    def test_user_cannot_approve_apps(self):
        """Test regular user cannot approve apps."""
        from app.core.exceptions import ForbiddenError
        
        user = User(
            id="user-123",
            email="user@example.com",
            username="user",
            hashed_password="hashed",
            role=UserRole.USER,
            is_active=True,
        )
        
        dependency = require_roles([UserRole.ADMIN])
        
        with pytest.raises(ForbiddenError):
            dependency(current_user=user)
