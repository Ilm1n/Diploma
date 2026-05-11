from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.boards.repository import BoardRepository
from src.realtimev1.domain_helpers import dump_task
from src.realtimev1.events import RealtimeEventType, RealtimeScope
from src.realtimev1.publisher import DomainEventPublisher
from src.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class TaskCreated(DomainEvent):
    task_id: int


class BoardsDomainEventDispatcher:
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        event_publisher: DomainEventPublisher,
    ) -> None:
        self._session_factory = session_factory
        self._event_publisher = event_publisher

    async def dispatch(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            if isinstance(event, TaskCreated):
                await self._publish_task_created(event)

    async def _publish_task_created(self, event: TaskCreated) -> None:
        async with self._session_factory() as session:
            repository = BoardRepository(session)
            task = await repository.get_task_with_tags(event.task_id)
            if task is None:
                return
            actor_user_id = event.actor_user_id
            if actor_user_id is None:
                actor_user_id = task.author_id
            if actor_user_id is None:
                return

            await self._event_publisher.publish_event(
                event_type=RealtimeEventType.TASK_CREATED,
                scope=RealtimeScope.PROJECT,
                actor_user_id=actor_user_id,
                project_id=task.project_id,
                payload={"task": dump_task(task)},
                client_mutation_id=event.client_mutation_id,
            )

            affected_user_ids = await repository.get_project_member_user_ids(
                task.project_id
            )
            if not affected_user_ids:
                return

            project_updated_at = await repository.get_project_updated_at(
                task.project_id
            )
            await self._event_publisher.publish_event(
                event_type=RealtimeEventType.PROJECT_LIST_ITEM_UPDATED,
                scope=RealtimeScope.USER,
                actor_user_id=actor_user_id,
                user_ids=affected_user_ids,
                project_id=task.project_id,
                payload={
                    "projectId": task.project_id,
                    "updatedAt": project_updated_at,
                    "reason": str(RealtimeEventType.TASK_CREATED),
                },
                client_mutation_id=event.client_mutation_id,
            )
