from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from src.projects.models import ProjectMember
from src.tags.models import Tag

POSITION_GAP = 65536.0
MIN_POSITION_DELTA = 0.001


class BoardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_board(
            self,
            project_id: int,
    ) -> Sequence[BoardColumn]:
        stmt = (
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(BoardColumn.position.asc())
            .options(
                selectinload(BoardColumn.tasks).selectinload(Task.tags)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_column(
            self,
            project_id: int,
            data: ColumnCreate,
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
        await self.session.commit()
        return new_column

    async def update_column(
            self,
            column: BoardColumn,
            data: ColumnUpdate,
    ) -> BoardColumn:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(column, key, value)

        self.session.add(column)
        await touch_project(self.session, column.project_id)
        await self.session.commit()
        return column

    async def delete_column(self, column: BoardColumn) -> None:
        await self.session.delete(column)
        await touch_project(self.session, column.project_id)
        await self.session.commit()

    async def reorder_columns(
            self,
            project_id: int,
            data: ColumnReorderRequest,
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
            await self.session.commit()

    async def create_task(
            self,
            project_id: int,
            column_id: int,
            data: TaskCreate,
            author_id: int,
    ) -> Task:
        column = await self.session.get(BoardColumn, column_id)
        if not column:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Column not found")

        if column.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Column belongs to another project")

        if column.tasks_limit is not None:
            count_query = select(func.count()).select_from(Task).where(
                Task.column_id == column_id)
            current_count = await self.session.scalar(count_query)
            if current_count >= column.tasks_limit:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Column '{column.name}' limit reached ({column.tasks_limit})",
                )

        if data.assignee_id:
            member_exists = await self.session.scalar(
                select(1).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == data.assignee_id,
                ).limit(1)
            )
            if not member_exists:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Assignee is not a project member")

        max_pos_query = select(func.max(Task.position)).where(
            Task.column_id == column_id)
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
            tags = (await self.session.execute(
                select(Tag).where(
                    Tag.id.in_(data.tag_ids),
                    Tag.project_id == project_id
                )
            )).scalars().all()

            if len(tags) != len(data.tag_ids):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid tag IDs")
            new_task.tags = list(tags)

        self.session.add(new_task)
        await touch_project(self.session, project_id)
        await self.session.commit()

        return await self._get_task_with_tags(new_task.id)

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
    ) -> Task:
        if task.column_id != data.new_column_id:
            target_col = await self.session.get(BoardColumn, data.new_column_id)
            if not target_col or target_col.project_id != task.project_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid target column")

            if target_col.tasks_limit is not None:
                cnt = await self.session.scalar(
                    select(func.count()).select_from(Task).where(
                        Task.column_id == data.new_column_id)
                )
                if cnt >= target_col.tasks_limit:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail="Column limit reached")

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
            await self.session.commit()
            return task

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to calculate position")

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
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Anchor task not found")

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
    ) -> Task:
        if data.assignee_id is not None and task.assignee_id != data.assignee_id:
            member_exists = await self.session.scalar(
                select(1).where(
                    ProjectMember.project_id == task.project_id,
                    ProjectMember.user_id == data.assignee_id,
                ).limit(1)
            )
            if not member_exists:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Assignee is not a project member")

        if data.tag_ids is not None:
            tags = (await self.session.execute(
                select(Tag).where(
                    Tag.id.in_(data.tag_ids),
                    Tag.project_id == task.project_id
                )
            )).scalars().all()
            if len(tags) != len(data.tag_ids):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid tag IDs")
            task.tags = list(tags)

        for key, value in data.model_dump(exclude_unset=True,
                                          exclude={"tag_ids"}).items():
            setattr(task, key, value)

        task.updated_at = datetime.now(timezone.utc)
        self.session.add(task)
        await touch_project(self.session, task.project_id)
        await self.session.commit()

        return await self._get_task_with_tags(task.id)

    async def delete_task(self, task: Task) -> None:
        await self.session.delete(task)
        await touch_project(self.session, task.project_id)
        await self.session.commit()

    async def _get_task_with_tags(self, task_id: int) -> Task:
        stmt = select(Task).where(Task.id == task_id).options(
            selectinload(Task.tags))
        result = await self.session.execute(stmt)
        return result.scalar_one()


def get_board_service(
        session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> BoardService:
    return BoardService(session)