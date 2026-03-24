from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from src.realtimev1.events import RealtimeDeliveryMessage

DeliveryConsumer = Callable[[RealtimeDeliveryMessage], Awaitable[None]]


class EventBus(Protocol):
    async def start(self, consumer: DeliveryConsumer) -> None: ...

    async def stop(self) -> None: ...

    async def publish(self, message: RealtimeDeliveryMessage) -> None: ...
