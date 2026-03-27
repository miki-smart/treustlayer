from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.modules.webhook.domain.entities.webhook_entities import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookSubscription,
)


class WebhookSubscriptionRepository(ABC):
    @abstractmethod
    async def create(self, sub: WebhookSubscription) -> WebhookSubscription: ...

    @abstractmethod
    async def get_by_id(self, sub_id: str) -> Optional[WebhookSubscription]: ...

    @abstractmethod
    async def get_by_event_type(self, event_type: str) -> List[WebhookSubscription]: ...

    @abstractmethod
    async def get_by_client_id(self, client_id: str) -> List[WebhookSubscription]: ...

    @abstractmethod
    async def deactivate(self, sub_id: str) -> None: ...

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 50) -> List[WebhookSubscription]: ...


class WebhookDeliveryRepository(ABC):
    @abstractmethod
    async def create(self, delivery: WebhookDelivery) -> WebhookDelivery: ...

    @abstractmethod
    async def update(self, delivery: WebhookDelivery) -> WebhookDelivery: ...

    @abstractmethod
    async def get_pending(self, limit: int = 50) -> List[WebhookDelivery]: ...

    @abstractmethod
    async def get_retryable(
        self, as_of: datetime, limit: int = 50
    ) -> List[WebhookDelivery]: ...

    @abstractmethod
    async def get_by_id(self, delivery_id: str) -> Optional[WebhookDelivery]: ...
