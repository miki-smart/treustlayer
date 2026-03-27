"""
Unit tests for Audit Logger service.
"""
import pytest
from unittest.mock import AsyncMock

from app.modules.audit.application.services.audit_logger import AuditLogger
from app.modules.audit.domain.entities.audit_entry import AuditEntry


class TestAuditLogger:
    """Test AuditLogger service."""
    
    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def audit_logger(self, mock_repo):
        """Create audit logger instance."""
        return AuditLogger(audit_repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_log_user_action(self, audit_logger, mock_repo):
        """Test logging user action."""
        mock_repo.create.return_value = AuditEntry(
            action="user.created",
            resource_type="user",
            actor_id="admin-123",
            resource_id="user-456",
        )
        
        result = await audit_logger.log(
            action="user.created",
            resource_type="user",
            actor_id="admin-123",
            resource_id="user-456",
            metadata={"ip_address": "127.0.0.1"},
        )
        
        assert result.action == "user.created"
        assert result.actor_id == "admin-123"
        mock_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_system_action(self, audit_logger, mock_repo):
        """Test logging system action (no actor)."""
        mock_repo.create.return_value = AuditEntry(
            action="system.cleanup",
            resource_type="session",
            actor_id=None,
        )
        
        result = await audit_logger.log(
            action="system.cleanup",
            resource_type="session",
            actor_id=None,
            metadata={"deleted_count": 10},
        )
        
        assert result.action == "system.cleanup"
        assert result.actor_id is None
        mock_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_with_changes(self, audit_logger, mock_repo):
        """Test logging with before/after changes."""
        mock_repo.create.return_value = AuditEntry(
            action="user.updated",
            resource_type="user",
            actor_id="user-123",
            resource_id="user-123",
            changes={"email": {"old": "old@example.com", "new": "new@example.com"}},
        )
        
        result = await audit_logger.log(
            action="user.updated",
            resource_type="user",
            actor_id="user-123",
            resource_id="user-123",
            changes={"email": {"old": "old@example.com", "new": "new@example.com"}},
        )
        
        assert "email" in result.changes
        assert result.changes["email"]["old"] == "old@example.com"
        assert result.changes["email"]["new"] == "new@example.com"
