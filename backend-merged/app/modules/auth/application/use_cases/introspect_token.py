"""
IntrospectTokenUseCase — RFC 7662 token introspection.
"""
import logging
from typing import Any, Dict

from jose import JWTError

from app.core.security import decode_token

logger = logging.getLogger(__name__)


class IntrospectTokenUseCase:
    """
    Token introspection endpoint (RFC 7662).
    
    Allows resource servers to validate access tokens.
    """
    
    async def execute(self, token: str) -> Dict[str, Any]:
        """
        Introspect token and return claims.
        
        Args:
            token: Access token to introspect
        
        Returns:
            Dict with 'active' boolean and token claims if valid
        """
        try:
            claims = decode_token(token)
            
            # Token is valid
            return {
                "active": True,
                **claims,
            }
        
        except JWTError as e:
            logger.debug(f"Token introspection failed: {e}")
            return {"active": False}
