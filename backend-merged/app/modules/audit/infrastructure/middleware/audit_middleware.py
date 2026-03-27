"""
Audit middleware — automatic audit logging for API requests.
"""
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic audit logging.
    
    Logs all state-changing operations (POST, PUT, PATCH, DELETE).
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit trail."""
        start_time = time.time()
        
        # Extract actor from JWT
        actor_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                claims = decode_token(token)
                actor_id = claims.get("sub")
            except Exception:
                pass
        
        # Process request
        response = await call_next(request)
        
        # Log state-changing operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"] and response.status_code < 400:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"AUDIT: {request.method} {request.url.path} by {actor_id or 'anonymous'} "
                f"[{response.status_code}] {duration_ms:.2f}ms"
            )
        
        return response
