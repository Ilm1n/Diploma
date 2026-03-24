from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.encoders import jsonable_encoder

from src.logger import get_logger
from src.realtimev1.events import (
    RealtimeAudience,
    RealtimeDeliveryMessage,
    RealtimeEventEnvelope,
    RealtimeEventType,
    RealtimeScope,
    new_event_envelope,
)

logger = get_logger("src.realtimev1.publisher")

if TYPE_CHECKING:
    from src.realtimev1.runtime import RealtimeRuntime


class DomainEventPublisher:
    def __init__(self, runtime: RealtimeRuntime | None):
        self._runtime = runtime

    async def publish_event(
        self,
        *,
        event_type: str | RealtimeEventType,
        scope: RealtimeScope,
        actor_user_id: int,
        payload: dict,
        project_id: int | None = None,
        user_ids: list[int] | None = None,
        audience: RealtimeAudience = RealtimeAudience.ALL,
        exclude_user_ids: list[int] | None = None,
        client_mutation_id: str | None = None,
    ) -> None:
        if not self._runtime:
            return

        envelope = new_event_envelope(
            event_type=event_type,
            scope=scope,
            actor_user_id=actor_user_id,
            payload=jsonable_encoder(payload),
            project_id=project_id,
            client_mutation_id=client_mutation_id,
        )
        await self.publish_delivery(
            envelope=envelope,
            user_ids=user_ids or [],
            project_id=project_id,
            audience=audience,
            exclude_user_ids=exclude_user_ids or [],
        )

    async def publish_delivery(
        self,
        *,
        envelope: RealtimeEventEnvelope,
        user_ids: list[int],
        project_id: int | None,
        audience: RealtimeAudience,
        exclude_user_ids: list[int],
    ) -> None:
        if not self._runtime:
            return

        delivery = RealtimeDeliveryMessage(
            envelope=envelope,
            user_ids=user_ids,
            project_id=project_id,
            audience=audience,
            exclude_user_ids=exclude_user_ids,
        )

        try:
            await self._runtime.publish(delivery)
        except Exception as exc:
            logger.exception("Realtime publish failed, fallback to local delivery", exc_info=exc)
            await self._runtime.dispatch_local(delivery)
