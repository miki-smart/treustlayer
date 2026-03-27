"""
Unit tests for Session Management.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from app.modules.auth.domain.entities.refresh_token import RefreshToken


class TestSessionManagement:
    """Test session management operations."""
    
    @pytest.fixture
    def mock_auth_repo(self):
        """Create mock auth repository."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_list_active_sessions(self, mock_auth_repo):
        """Test listing active sessions."""
        mock_sessions = [
            RefreshToken(
                id=f"token-{i}",
                user_id="user-123",
                client_id="client-123",
                token_hash=f"hash-{i}",
                scopes=["openid"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                is_revoked=False,
                device_info=f"Device {i}",
                ip_address="127.0.0.1",
            )
            for i in range(3)
        ]
        mock_auth_repo.list_refresh_tokens_by_user.return_value = mock_sessions
        
        sessions = await mock_auth_repo.list_refresh_tokens_by_user("user-123")
        
        assert len(sessions) == 3
        assert all(s.user_id == "user-123" for s in sessions)
        assert all(not s.is_revoked for s in sessions)
    
    @pytest.mark.asyncio
    async def test_revoke_specific_session(self, mock_auth_repo):
        """Test revoking specific session."""
        session = RefreshToken(
            id="token-123",
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        mock_auth_repo.get_refresh_token_by_id.return_value = session
        
        session.revoke()
        await mock_auth_repo.update_refresh_token(session)
        
        assert session.is_revoked is True
        mock_auth_repo.update_refresh_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_all_sessions(self, mock_auth_repo):
        """Test revoking all user sessions."""
        mock_sessions = [
            RefreshToken(
                id=f"token-{i}",
                user_id="user-123",
                client_id="client-123",
                token_hash=f"hash-{i}",
                scopes=["openid"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                is_revoked=False,
            )
            for i in range(5)
        ]
        mock_auth_repo.list_refresh_tokens_by_user.return_value = mock_sessions
        
        await mock_auth_repo.revoke_all_refresh_tokens("user-123")
        
        mock_auth_repo.revoke_all_refresh_tokens.assert_called_once_with("user-123")
    
    @pytest.mark.asyncio
    async def test_session_with_device_info(self, mock_auth_repo):
        """Test session includes device information."""
        session = RefreshToken(
            user_id="user-123",
            client_id="client-123",
            token_hash="hash",
            scopes=["openid"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            device_info="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ip_address="192.168.1.100",
        )
        
        assert session.device_info is not None
        assert session.ip_address == "192.168.1.100"
        assert "Windows" in session.device_info
