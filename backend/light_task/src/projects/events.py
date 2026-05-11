from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from src.projects.repository import ProjectRepository
from src.projects.constants import ProjectRole
from src.realtimev1.events import RealtimeEventType, RealtimeScope
from src.realtimev1.publisher import DomainEventPublisher
from src.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class MemberRemoved(DomainEvent):
    user_id: int
    remaining_user_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class MemberRoleChanged(DomainEvent):
    user_id: int
    role: ProjectRole
    previous_role: ProjectRole
    affected_user_ids: list[int] = field(default_factory=list)


class ProjectsDomainEventDispatcher:
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        event_publisher: DomainEventPublisher,
    ) -> None:
        self._session_factory = session_factory
        self._event_publisher = event_publisher

    async def dispatch(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            if isinstance(event, MemberRemoved):
                await self._publish_member_removed(event)
            if isinstance(event, MemberRoleChanged):
                await self._publish_member_role_changed(event)

    async def _publish_member_removed(self, event: MemberRemoved) -> None:
        if event.project_id is None or event.actor_user_id is None:
            return

        await self._event_publisher.publish_event(
            event_type=RealtimeEventType.MEMBER_REMOVED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=event.actor_user_id,
            project_id=event.project_id,
            payload={"userId": event.user_id},
            client_mutation_id=event.client_mutation_id,
        )
        await self._event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_REMOVED_FROM_USER,
            scope=RealtimeScope.USER,
            actor_user_id=event.actor_user_id,
            project_id=event.project_id,
            user_ids=[event.user_id],
            payload={"projectId": event.project_id},
            client_mutation_id=event.client_mutation_id,
        )
        async with self._session_factory() as session:
            repository = ProjectRepository(session)
            await self._publish_project_list_item_updated(
                repository=repository,
                project_id=event.project_id,
                actor_user_id=event.actor_user_id,
                user_ids=event.remaining_user_ids,
                reason=RealtimeEventType.MEMBER_REMOVED,
                client_mutation_id=event.client_mutation_id,
            )

    async def _publish_member_role_changed(self, event: MemberRoleChanged) -> None:
        if event.project_id is None or event.actor_user_id is None:
            return

        await self._event_publisher.publish_event(
            event_type=RealtimeEventType.MEMBER_ROLE_CHANGED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=event.actor_user_id,
            project_id=event.project_id,
            payload={
                "userId": event.user_id,
                "role": event.role,
                "previousRole": event.previous_role,
            },
            client_mutation_id=event.client_mutation_id,
        )
        async with self._session_factory() as session:
            repository = ProjectRepository(session)
            await self._publish_project_list_item_updated(
                repository=repository,
                project_id=event.project_id,
                actor_user_id=event.actor_user_id,
                user_ids=event.affected_user_ids,
                reason=RealtimeEventType.MEMBER_ROLE_CHANGED,
                client_mutation_id=event.client_mutation_id,
            )

    async def _publish_project_list_item_updated(
        self,
        *,
        repository: ProjectRepository,
        project_id: int,
        actor_user_id: int,
        user_ids: list[int],
        reason: RealtimeEventType,
        client_mutation_id: str | None,
    ) -> None:
        if not user_ids:
            return

        project_updated_at = await repository.get_project_updated_at(project_id)
        await self._event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_LIST_ITEM_UPDATED,
            scope=RealtimeScope.USER,
            actor_user_id=actor_user_id,
            user_ids=user_ids,
            project_id=project_id,
            payload={
                "projectId": project_id,
                "updatedAt": project_updated_at,
                "reason": str(reason),
            },
            client_mutation_id=client_mutation_id,
        )
