"""
In-process event bus for cross-module async communication.

Design:
  - Publish/Subscribe pattern with named event types.
  - Supports sync and async handlers transparently.
  - Idempotency guard via in-memory set (swap for DB-backed store in production).
  - Full error isolation: one failing handler does not affect others.
"""
import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Base class for all domain events. Pure Python — no framework imports."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def event_type(self) -> str:
        return type(self).__name__


class EventBus:
    def __init__(self) -> None:
        self._handlers: defaultdict[str, list[Callable]] = defaultdict(list)
        # In-memory idempotency store — replace with Redis/DB in production.
        self._processed_ids: set[str] = set()

    def subscribe(self, event_class: type, handler: Callable) -> None:
        """Register a handler for an event class."""
        self._handlers[event_class.__name__].append(handler)
        logger.debug(
            "EventBus: subscribed %s → %s",
            event_class.__name__,
            handler.__qualname__,
        )

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all registered handlers.
        Idempotent: duplicate event_ids are silently dropped.
        """
        if event.event_id in self._processed_ids:
            logger.warning(
                "EventBus: duplicate event %s [%s] — skipped",
                event.event_type,
                event.event_id,
            )
            return

        self._processed_ids.add(event.event_id)
        logger.info(
            "EventBus: publishing %s [%s]", event.event_type, event.event_id
        )

        for handler in self._handlers.get(event.event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as exc:
                logger.error(
                    "EventBus: handler %s failed for %s: %s",
                    handler.__qualname__,
                    event.event_type,
                    exc,
                    exc_info=True,
                )


# Singleton event bus — imported by all modules.
event_bus = EventBus()
