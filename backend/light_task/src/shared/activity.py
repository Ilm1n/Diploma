from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from src.shared.events import DomainEvent


class ActivityLogger(Protocol):
    async def log(self, events: Sequence[DomainEvent]) -> None:
        pass


class NoopActivityLogger:
    async def log(self, events: Sequence[DomainEvent]) -> None:
        return None
