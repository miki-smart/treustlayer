from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.kyc.domain.entities.kyc_verification import KYCStatus, KYCVerification


class KYCRepository(ABC):
    @abstractmethod
    async def create(self, kyc: KYCVerification) -> KYCVerification: ...

    @abstractmethod
    async def get_by_id(self, kyc_id: str) -> Optional[KYCVerification]: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[KYCVerification]: ...

    @abstractmethod
    async def list_by_status(
        self, status: KYCStatus, skip: int = 0, limit: int = 50
    ) -> List[KYCVerification]: ...

    @abstractmethod
    async def list_all(
        self, skip: int = 0, limit: int = 50
    ) -> List[KYCVerification]: ...

    @abstractmethod
    async def update(self, kyc: KYCVerification) -> KYCVerification: ...
