"""
Unit tests for Analytics Service.
"""
import pytest
from unittest.mock import AsyncMock

from app.modules.dashboard.application.services.analytics_service import (
    AnalyticsService,
)
from app.modules.identity.domain.entities.user import User, UserRole
from app.modules.kyc.domain.entities.kyc_verification import (
    KYCVerification,
    KYCStatus,
)
from app.modules.app_registry.domain.entities.app import App


class TestAnalyticsService:
    """Test AnalyticsService."""
    
    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "user_repo": AsyncMock(),
            "kyc_repo": AsyncMock(),
            "app_repo": AsyncMock(),
            "auth_repo": AsyncMock(),
        }
    
    @pytest.fixture
    def analytics_service(self, mock_repos):
        """Create analytics service instance."""
        return AnalyticsService(
            user_repo=mock_repos["user_repo"],
            kyc_repo=mock_repos["kyc_repo"],
            app_repo=mock_repos["app_repo"],
            auth_repo=mock_repos["auth_repo"],
        )
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, analytics_service, mock_repos):
        """Test getting dashboard statistics."""
        mock_users = [
            User(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                username=f"user{i}",
                hashed_password="hashed",
                role=UserRole.USER,
                is_active=True,
                is_email_verified=(i % 2 == 0),
            )
            for i in range(10)
        ]
        
        mock_kyc_pending = [
            KYCVerification(user_id=f"user-{i}", status=KYCStatus.PENDING)
            for i in range(3)
        ]
        
        mock_kyc_approved = [
            KYCVerification(user_id=f"user-{i}", status=KYCStatus.APPROVED)
            for i in range(5)
        ]
        
        mock_apps = [
            App(
                name=f"App {i}",
                owner_id="user-1",
                allowed_scopes=["openid"],
                redirect_uris=["http://localhost:3000"],
                is_approved=(i % 2 == 0),
            )
            for i in range(4)
        ]
        
        mock_repos["user_repo"].list_all.return_value = mock_users
        mock_repos["kyc_repo"].list_by_status.side_effect = [
            mock_kyc_pending,  # PENDING
            [],  # IN_REVIEW
            mock_kyc_approved,  # APPROVED
            [],  # REJECTED
        ]
        mock_repos["app_repo"].list_all.return_value = mock_apps
        mock_repos["auth_repo"].count_active_sessions.return_value = 15
        
        stats = await analytics_service.get_dashboard_stats()
        
        assert stats["total_users"] == 10
        assert stats["verified_users"] == 5
        assert stats["kyc_pending"] == 3
        assert stats["kyc_approved"] == 5
        assert stats["total_apps"] == 4
        assert stats["apps_pending"] == 2
        assert stats["active_sessions"] == 15
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats_empty(self, analytics_service, mock_repos):
        """Test dashboard stats with no data."""
        mock_repos["user_repo"].list_all.return_value = []
        mock_repos["kyc_repo"].list_by_status.return_value = []
        mock_repos["app_repo"].list_all.return_value = []
        mock_repos["auth_repo"].count_active_sessions.return_value = 0
        
        stats = await analytics_service.get_dashboard_stats()
        
        assert stats["total_users"] == 0
        assert stats["verified_users"] == 0
        assert stats["kyc_pending"] == 0
        assert stats["total_apps"] == 0
        assert stats["active_sessions"] == 0
