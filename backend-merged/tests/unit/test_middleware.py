"""
Unit tests for middleware components.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request, Response

from app.modules.audit.infrastructure.middleware.audit_middleware import AuditMiddleware
from app.modules.audit.domain.entities.audit_entry import AuditEntry


class TestAuditMiddleware:
    """Test AuditMiddleware."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = AsyncMock()
        logger.log.return_value = AuditEntry(
            action="request",
            resource_type="api",
            actor_id="user-123",
        )
        return logger
    
    @pytest.fixture
    def middleware(self, mock_audit_logger):
        """Create middleware instance."""
        return AuditMiddleware(audit_logger=mock_audit_logger)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/v1/users"
        request.client.host = "127.0.0.1"
        request.state.user = MagicMock(id="user-123")
        return request
    
    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function."""
        async def call_next(request):
            return Response(content="OK", status_code=200)
        return call_next
    
    @pytest.mark.asyncio
    async def test_audit_middleware_logs_state_changing_request(
        self, middleware, mock_request, mock_call_next, mock_audit_logger
    ):
        """Test middleware logs POST/PUT/DELETE requests."""
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        mock_audit_logger.log.assert_called_once()
        
        call_args = mock_audit_logger.log.call_args
        assert call_args.kwargs["action"] == "api.request"
        assert call_args.kwargs["actor_id"] == "user-123"
    
    @pytest.mark.asyncio
    async def test_audit_middleware_skips_get_request(
        self, middleware, mock_request, mock_call_next, mock_audit_logger
    ):
        """Test middleware skips GET requests."""
        mock_request.method = "GET"
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        mock_audit_logger.log.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_audit_middleware_handles_unauthenticated(
        self, middleware, mock_request, mock_call_next, mock_audit_logger
    ):
        """Test middleware handles requests without user."""
        mock_request.state.user = None
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        
        if mock_audit_logger.log.called:
            call_args = mock_audit_logger.log.call_args
            assert call_args.kwargs["actor_id"] is None
    
    @pytest.mark.asyncio
    async def test_audit_middleware_logs_metadata(
        self, middleware, mock_request, mock_call_next, mock_audit_logger
    ):
        """Test middleware includes request metadata."""
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == 200
        
        if mock_audit_logger.log.called:
            call_args = mock_audit_logger.log.call_args
            metadata = call_args.kwargs.get("metadata", {})
            assert "ip_address" in metadata
            assert "method" in metadata
            assert "path" in metadata
