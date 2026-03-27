from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.biometric.domain.entities.biometric_record import BiometricRecord, BiometricType


class BiometricRepository(ABC):
    @abstractmethod
    async def create(self, record: BiometricRecord) -> BiometricRecord: ...

    @abstractmethod
    async def get_by_id(self, record_id: str) -> Optional[BiometricRecord]: ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> List[BiometricRecord]: ...

    @abstractmethod
    async def list_by_user_and_type(self, user_id: str, type: BiometricType) -> List[BiometricRecord]: ...

    @abstractmethod
    async def get_verified_by_user_and_type(self, user_id: str, type: BiometricType) -> Optional[BiometricRecord]: ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 50) -> List[BiometricRecord]: ...

    @abstractmethod
    async def update(self, record: BiometricRecord) -> BiometricRecord: ...

    @abstractmethod
    async def delete(self, record_id: str) -> None: ...
