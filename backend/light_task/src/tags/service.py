from collections.abc import Sequence
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import db_helper
from src.logger import board_logger
from src.errors import ErrorCode
from src.tags.models import Tag
from src.tags.schemas import TagCreate, TagUpdate
from src.common.touch import touch_project
from src.projects.models import Project
from src.realtimev1.dependencies import get_event_publisher
from src.realtimev1.domain_helpers import dump_tag, get_project_member_user_ids
from src.realtimev1.events import RealtimeEventType, RealtimeScope
from src.realtimev1.publisher import DomainEventPublisher


class TagService:
    def __init__(self, session: AsyncSession, event_publisher: DomainEventPublisher):
        self.session = session
        self.event_publisher = event_publisher

    async def get_project_tags(
        self,
        project_id: int,
    ) -> Sequence[Tag]:
        query = select(Tag).where(Tag.project_id == project_id).order_by(Tag.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_tag(
        self,
        project_id: int,
        data: TagCreate,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> Tag:
        query = select(Tag).where(
            Tag.project_id == project_id,
            Tag.name == data.name,
        )
        existing = await self.session.scalar(query)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.TAG_ALREADY_EXISTS,
            )

        tag = Tag(
            name=data.name,
            color=data.color,
            project_id=project_id,
        )
        self.session.add(tag)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            await self.session.refresh(tag)
            board_logger.info(f"Tag created: {tag.id} in project {project_id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to create tag in project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.TAG_CREATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"tag": dump_tag(tag)},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.TAG_CREATED,
            client_mutation_id=client_mutation_id,
        )
        return tag

    async def update_tag(
        self,
        tag: Tag,
        data: TagUpdate,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> Tag:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tag, key, value)

        self.session.add(tag)
        await touch_project(self.session, tag.project_id)
        try:
            await self.session.commit()
            await self.session.refresh(tag)
            await self.event_publisher.publish_event(
                event_type=RealtimeEventType.TAG_UPDATED,
                scope=RealtimeScope.PROJECT,
                actor_user_id=actor_user_id,
                project_id=tag.project_id,
                payload={"tag": dump_tag(tag)},
                client_mutation_id=client_mutation_id,
            )
            await self._publish_project_list_item_updated(
                project_id=tag.project_id,
                actor_user_id=actor_user_id,
                reason=RealtimeEventType.TAG_UPDATED,
                client_mutation_id=client_mutation_id,
            )
            return tag
        except Exception:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.TAG_ALREADY_EXISTS,
            )

    async def delete_tag(
        self,
        tag: Tag,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> None:
        project_id = tag.project_id
        tag_id = tag.id
        await self.session.delete(tag)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            board_logger.info(f"Tag deleted: {tag_id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to delete tag {tag_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.TAG_DELETED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"tagId": tag_id},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.TAG_DELETED,
            client_mutation_id=client_mutation_id,
        )

    async def _publish_project_list_item_updated(
        self,
        *,
        project_id: int,
        actor_user_id: int,
        reason: str | RealtimeEventType,
        client_mutation_id: str | None,
    ) -> None:
        affected_user_ids = await get_project_member_user_ids(self.session, project_id)
        if not affected_user_ids:
            return

        project_updated_at = await self.session.scalar(
            select(Project.updated_at).where(Project.id == project_id)
        )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_LIST_ITEM_UPDATED,
            scope=RealtimeScope.USER,
            actor_user_id=actor_user_id,
            user_ids=affected_user_ids,
            project_id=project_id,
            payload={
                "projectId": project_id,
                "updatedAt": project_updated_at,
                "reason": str(reason),
            },
            client_mutation_id=client_mutation_id,
        )


def get_tag_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> TagService:
    return TagService(session, event_publisher)
