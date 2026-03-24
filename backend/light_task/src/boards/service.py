from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.projects.constants import ProjectRole
from src.boards.models import BoardColumn, Task
from src.boards.schemas import (
    ColumnCreate,
    TaskCreate,
    TaskMove,
    TaskUpdate,
    ColumnReorderRequest,
    ColumnUpdate,
)
from src.common.touch import touch_project
from src.db.database import db_helper
from src.logger import board_logger
from src.errors import ErrorCode
from src.projects.models import Project, ProjectMember
from src.tags.models import Tag
from src.realtimev1.dependencies import get_event_publisher
from src.realtimev1.domain_helpers import (
    dump_column,
    dump_task,
    get_project_member_user_ids,
)
from src.realtimev1.events import RealtimeEventType, RealtimeScope
from src.realtimev1.publisher import DomainEventPublisher

POSITION_GAP = 65536.0
MIN_POSITION_DELTA = 0.001


class BoardService:
    def __init__(self, session: AsyncSession, event_publisher: DomainEventPublisher):
        self.session = session
        self.event_publisher = event_publisher

    async def get_board(
        self,
        project_id: int,
    ) -> Sequence[BoardColumn]:
        stmt = (
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(BoardColumn.position.asc())
            .options(selectinload(BoardColumn.tasks).selectinload(Task.tags))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_column(
        self,
        project_id: int,
        data: ColumnCreate,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> BoardColumn:
        query = select(func.max(BoardColumn.position)).where(
            BoardColumn.project_id == project_id
        )
        max_pos = await self.session.scalar(query) or 0.0

        new_column = BoardColumn(
            name=data.name,
            tasks_limit=data.tasks_limit,
            project_id=project_id,
            position=max_pos + POSITION_GAP,
            tasks=[],
        )
        self.session.add(new_column)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            await self.session.refresh(new_column)
            board_logger.info(
                f"Column created: {new_column.id} in project {project_id}"
            )
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to create column in project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.COLUMN_CREATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"column": dump_column(new_column)},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.COLUMN_CREATED,
            client_mutation_id=client_mutation_id,
        )
        return await self._get_column_with_tasks(new_column.id)

    async def update_column(
        self,
        column: BoardColumn,
        data: ColumnUpdate,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> BoardColumn:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(column, key, value)

        self.session.add(column)
        await touch_project(self.session, column.project_id)
        try:
            await self.session.commit()
            await self.session.refresh(column)
            board_logger.info(f"Column updated: {column.id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to update column {column.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.COLUMN_UPDATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=column.project_id,
            payload={"column": dump_column(column)},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=column.project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.COLUMN_UPDATED,
            client_mutation_id=client_mutation_id,
        )
        return await self._get_column_with_tasks(column.id)

    async def delete_column(
        self,
        column: BoardColumn,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> None:
        project_id = column.project_id
        column_id = column.id
        await self.session.delete(column)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            board_logger.info(f"Column deleted: {column_id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to delete column {column_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.COLUMN_DELETED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"columnId": column_id},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.COLUMN_DELETED,
            client_mutation_id=client_mutation_id,
        )

    async def reorder_columns(
        self,
        project_id: int,
        data: ColumnReorderRequest,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> None:
        stmt = select(BoardColumn).where(
            BoardColumn.project_id == project_id,
            BoardColumn.id.in_(data.column_ids),
        )
        columns = (await self.session.execute(stmt)).scalars().all()
        col_map = {col.id: col for col in columns}

        for index, col_id in enumerate(data.column_ids):
            if column := col_map.get(col_id):
                column.position = (index + 1) * POSITION_GAP
                self.session.add(column)

        if columns:
            await touch_project(self.session, columns[0].project_id)
            try:
                await self.session.commit()
                board_logger.info(f"Columns reordered in project {project_id}")
            except Exception as e:
                await self.session.rollback()
                board_logger.exception(
                    f"Failed to reorder columns in project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorCode.DATABASE_ERROR,
                )
            await self.event_publisher.publish_event(
                event_type=RealtimeEventType.COLUMNS_REORDERED,
                scope=RealtimeScope.PROJECT,
                actor_user_id=actor_user_id,
                project_id=project_id,
                payload={"columnOrder": data.column_ids},
                client_mutation_id=client_mutation_id,
            )
            await self._publish_project_list_item_updated(
                project_id=project_id,
                actor_user_id=actor_user_id,
                reason=RealtimeEventType.COLUMNS_REORDERED,
                client_mutation_id=client_mutation_id,
            )

    async def create_task(
        self,
        project_id: int,
        column_id: int,
        data: TaskCreate,
        author_id: int,
        client_mutation_id: str | None = None,
    ) -> Task:
        column = await self.session.get(BoardColumn, column_id)
        if not column:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.COLUMN_NOT_FOUND,
            )

        if column.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.COLUMN_BELONGS_ANOTHER_PROJECT,
            )

        if column.tasks_limit is not None:
            count_query = (
                select(func.count())
                .select_from(Task)
                .where(Task.column_id == column_id)
            )
            current_count = await self.session.scalar(count_query)
            if current_count >= column.tasks_limit:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=ErrorCode.COLUMN_TASK_LIMIT_REACHED,
                )

        if data.assignee_id:
            author_member = await self.session.scalar(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == author_id,
                )
            )

            if author_member and author_member.role == ProjectRole.MEMBER:
                if data.assignee_id != author_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=ErrorCode.MEMBERS_ONLY_OWN_TASKS,
                    )

            member_exists = await self.session.scalar(
                select(1)
                .where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == data.assignee_id,
                )
                .limit(1)
            )
            if not member_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorCode.ASSIGNEE_NOT_PROJECT_MEMBER,
                )

        max_pos_query = select(func.max(Task.position)).where(
            Task.column_id == column_id
        )
        max_pos = await self.session.scalar(max_pos_query) or 0.0

        new_task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            project_id=project_id,
            column_id=column_id,
            assignee_id=data.assignee_id,
            author_id=author_id,
            position=max_pos + POSITION_GAP,
        )

        if data.tag_ids:
            tags = (
                (
                    await self.session.execute(
                        select(Tag).where(
                            Tag.id.in_(data.tag_ids), Tag.project_id == project_id
                        )
                    )
                )
                .scalars()
                .all()
            )

            if len(tags) != len(data.tag_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorCode.INVALID_TAG_IDS,
                )
            new_task.tags = list(tags)

        self.session.add(new_task)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            board_logger.info(f"Task created: {new_task.id} in project {project_id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to create task in project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )

        task = await self._get_task_with_tags(new_task.id)
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.TASK_CREATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=author_id,
            project_id=project_id,
            payload={"task": dump_task(task)},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=author_id,
            reason=RealtimeEventType.TASK_CREATED,
            client_mutation_id=client_mutation_id,
        )
        return task

    async def get_project_tasks(
        self,
        project_id: int,
        assignee_id: int | None = None,
        tag_ids: list[int] | None = None,
        search: str | None = None,
    ) -> Sequence[Task]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .options(selectinload(Task.tags), selectinload(Task.assignee))
            .order_by(Task.updated_at.desc())
        )

        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)

        if search:
            stmt = stmt.where(
                or_(
                    Task.title.ilike(f"%{search}%"),
                    Task.description.ilike(f"%{search}%"),
                )
            )

        if tag_ids:
            stmt = stmt.join(Task.tags).where(Tag.id.in_(tag_ids)).distinct()

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def move_task(
        self,
        task: Task,
        data: TaskMove,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> Task:
        from_column_id = task.column_id
        if task.column_id != data.new_column_id:
            target_col = await self.session.get(BoardColumn, data.new_column_id)
            if not target_col or target_col.project_id != task.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorCode.INVALID_TARGET_COLUMN,
                )

            if target_col.tasks_limit is not None:
                cnt = await self.session.scalar(
                    select(func.count())
                    .select_from(Task)
                    .where(Task.column_id == data.new_column_id)
                )
                if cnt >= target_col.tasks_limit:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=ErrorCode.COLUMN_TASK_LIMIT_REACHED,
                    )

        attempts = 0
        while attempts < 2:
            attempts += 1
            new_position = await self._calculate_new_position(
                data.new_column_id, data.after_task_id
            )

            if new_position is None:
                await self._rebalance_column(data.new_column_id)
                continue

            task.column_id = data.new_column_id
            task.position = new_position
            task.updated_at = datetime.now(timezone.utc)

            self.session.add(task)
            await touch_project(self.session, task.project_id)
            try:
                await self.session.commit()
                board_logger.info(
                    f"Task {task.id} moved to column {data.new_column_id}"
                )
            except Exception as e:
                await self.session.rollback()
                board_logger.exception(f"Failed to move task {task.id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorCode.DATABASE_ERROR,
                )
            moved_task = await self._get_task_with_tags(task.id)
            await self.event_publisher.publish_event(
                event_type=RealtimeEventType.TASK_MOVED,
                scope=RealtimeScope.PROJECT,
                actor_user_id=actor_user_id,
                project_id=task.project_id,
                payload={
                    "task": dump_task(moved_task),
                    "fromColumnId": from_column_id,
                    "toColumnId": data.new_column_id,
                },
                client_mutation_id=client_mutation_id,
            )
            await self._publish_project_list_item_updated(
                project_id=task.project_id,
                actor_user_id=actor_user_id,
                reason=RealtimeEventType.TASK_MOVED,
                client_mutation_id=client_mutation_id,
            )
            return task

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.DATABASE_ERROR,
        )

    async def _calculate_new_position(
        self,
        column_id: int,
        after_task_id: int | None,
    ) -> float | None:
        if after_task_id is None:
            stmt = (
                select(Task.position)
                .where(Task.column_id == column_id)
                .order_by(Task.position.asc())
                .limit(1)
                .with_for_update()
            )
            first_pos = await self.session.scalar(stmt)

            if first_pos is None:
                return POSITION_GAP

            new_pos = first_pos / 2.0
            return new_pos if new_pos > MIN_POSITION_DELTA else None

        else:
            anchor_stmt = (
                select(Task.position)
                .where(Task.id == after_task_id, Task.column_id == column_id)
                .with_for_update()
            )
            anchor_pos = await self.session.scalar(anchor_stmt)

            if anchor_pos is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=ErrorCode.ANCHOR_TASK_NOT_FOUND,
                )

            next_stmt = (
                select(Task.position)
                .where(Task.column_id == column_id, Task.position > anchor_pos)
                .order_by(Task.position.asc())
                .limit(1)
                .with_for_update()
            )
            next_pos = await self.session.scalar(next_stmt)

            if next_pos is None:
                return anchor_pos + POSITION_GAP

            delta = next_pos - anchor_pos
            if delta <= MIN_POSITION_DELTA:
                return None

            return anchor_pos + (delta / 2.0)

    async def _rebalance_column(self, column_id: int):
        stmt = (
            select(Task)
            .where(Task.column_id == column_id)
            .order_by(Task.position.asc())
            .with_for_update()
        )
        tasks = (await self.session.execute(stmt)).scalars().all()

        for index, task in enumerate(tasks):
            task.position = (index + 1) * POSITION_GAP
            self.session.add(task)

        await self.session.flush()

    async def update_task(
        self,
        task: Task,
        data: TaskUpdate,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> Task:
        if data.assignee_id is not None and task.assignee_id != data.assignee_id:
            member_exists = await self.session.scalar(
                select(1)
                .where(
                    ProjectMember.project_id == task.project_id,
                    ProjectMember.user_id == data.assignee_id,
                )
                .limit(1)
            )
            if not member_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorCode.ASSIGNEE_NOT_PROJECT_MEMBER,
                )

        if data.tag_ids is not None:
            tags = (
                (
                    await self.session.execute(
                        select(Tag).where(
                            Tag.id.in_(data.tag_ids), Tag.project_id == task.project_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            if len(tags) != len(data.tag_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorCode.INVALID_TAG_IDS,
                )
            task.tags = list(tags)

        for key, value in data.model_dump(
            exclude_unset=True, exclude={"tag_ids"}
        ).items():
            setattr(task, key, value)

        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        await touch_project(self.session, task.project_id)
        try:
            await self.session.commit()
            board_logger.info(f"Task updated: {task.id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to update task {task.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )

        updated_task = await self._get_task_with_tags(task.id)
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.TASK_UPDATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=task.project_id,
            payload={"task": dump_task(updated_task)},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=task.project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.TASK_UPDATED,
            client_mutation_id=client_mutation_id,
        )
        return updated_task

    async def delete_task(
        self,
        task: Task,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> None:
        task_id = task.id
        project_id = task.project_id
        column_id = task.column_id
        await self.session.delete(task)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            board_logger.info(f"Task deleted: {task_id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to delete task {task_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.TASK_DELETED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"taskId": task_id, "columnId": column_id},
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.TASK_DELETED,
            client_mutation_id=client_mutation_id,
        )

    async def _get_task_with_tags(self, task_id: int) -> Task:
        stmt = select(Task).where(Task.id == task_id).options(selectinload(Task.tags))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _get_column_with_tasks(self, column_id: int) -> BoardColumn:
        stmt = (
            select(BoardColumn)
            .where(BoardColumn.id == column_id)
            .options(selectinload(BoardColumn.tasks).selectinload(Task.tags))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

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


def get_board_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> BoardService:
    return BoardService(session, event_publisher)
