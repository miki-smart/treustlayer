"""
ConsentRepository — repository interface for consent domain.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.consent.domain.entities.consent_record import ConsentRecord


class ConsentRepository(ABC):
    """Repository interface for consent records."""
    
    @abstractmethod
    async def create(self, consent: ConsentRecord) -> ConsentRecord:
        """Create new consent record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, consent_id: str) -> Optional[ConsentRecord]:
        """Get consent by ID."""
        pass
    
    @abstractmethod
    async def get_by_user_and_client(
        self, user_id: str, client_id: str
    ) -> Optional[ConsentRecord]:
        """Get consent by user and client."""
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: str) -> List[ConsentRecord]:
        """List all consents for a user."""
        pass
    
    @abstractmethod
    async def list_by_client(self, client_id: str) -> List[ConsentRecord]:
        """List all consents for a client."""
        pass
    
    @abstractmethod
    async def update(self, consent: ConsentRecord) -> ConsentRecord:
        """Update consent record."""
        pass
    
    @abstractmethod
    async def delete(self, consent_id: str) -> None:
        """Delete consent record."""
        pass
