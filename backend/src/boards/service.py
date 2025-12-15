from typing import Optional, Sequence
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, attributes

from src.projects.models import ProjectMember
from src.boards.models import BoardColumn, Task
from src.boards.schemas import ColumnCreate, TaskCreate, TaskMove

POSITION_GAP = 65536.0
MIN_POSITION_DELTA = 0.002


class BoardService:
    @staticmethod
    async def get_board(
        session: AsyncSession, project_id: int
    ) -> Sequence[BoardColumn]:
        stmt = (
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(BoardColumn.position.asc())
            .options(selectinload(BoardColumn.tasks))
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_column(
        session: AsyncSession, project_id: int, data: ColumnCreate
    ) -> BoardColumn:

        query = select(func.max(BoardColumn.position)).where(
            BoardColumn.project_id == project_id
        )
        max_pos = await session.scalar(query) or 0.0

        new_column = BoardColumn(
            name=data.name,
            project_id=project_id,
            position=max_pos + POSITION_GAP,
        )
        session.add(new_column)
        await session.commit()
        attributes.set_committed_value(new_column, "tasks", [])
        return new_column

    @staticmethod
    async def create_task(
        session: AsyncSession,
        project_id: int,
        column_id: int,
        data: TaskCreate,
        author_id: int,
    ) -> Task:
        if data.assignee_id is not None:
            stmt = select(1).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == data.assignee_id,
            )
            if not (await session.scalar(stmt)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee is not a member of this project.",
                )

        query = select(func.max(Task.position)).where(Task.column_id == column_id)
        max_pos = await session.scalar(query) or 0.0

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
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        return new_task

    @staticmethod
    async def move_task(session: AsyncSession, task: Task, data: TaskMove) -> Task:
        if task.column_id != data.new_column_id:
            col_check = await session.get(BoardColumn, data.new_column_id)
            if not col_check or col_check.project_id != task.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target column invalid or belongs to another project",
                )

        attempts = 0
        while attempts < 2:
            attempts += 1
            new_position = await BoardService._calculate_new_position(
                session, data.new_column_id, data.after_task_id
            )

            if new_position is None:
                await BoardService._rebalance_column(session, data.new_column_id)
                continue

            task.column_id = data.new_column_id
            task.position = new_position
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to move task due to position calculation error.",
        )

    @staticmethod
    async def _calculate_new_position(
        session: AsyncSession, column_id: int, after_task_id: Optional[int]
    ) -> Optional[float]:
        if after_task_id is None:
            stmt = (
                select(Task.position)
                .where(Task.column_id == column_id)
                .order_by(Task.position.asc())
                .limit(1)
                .with_for_update()
            )
            first_pos = await session.scalar(stmt)

            if first_pos is None:
                return POSITION_GAP

            new_pos = first_pos / 2.0
            return new_pos if new_pos > MIN_POSITION_DELTA else None

        else:
            prev_task_stmt = (
                select(Task.position)
                .where(Task.id == after_task_id, Task.column_id == column_id)
                .with_for_update()
            )
            prev_pos = await session.scalar(prev_task_stmt)

            if prev_pos is None:
                raise HTTPException(
                    status_code=409, detail="Anchor task not found in target column"
                )

            next_task_stmt = (
                select(Task.position)
                .where(Task.column_id == column_id, Task.position > prev_pos)
                .order_by(Task.position.asc())
                .limit(1)
                .with_for_update()
            )
            next_pos = await session.scalar(next_task_stmt)

            if next_pos is None:
                return prev_pos + POSITION_GAP

            delta = next_pos - prev_pos
            return (prev_pos + delta / 2.0) if delta > MIN_POSITION_DELTA else None

    @staticmethod
    async def _rebalance_column(session: AsyncSession, column_id: int):
        stmt = (
            select(Task)
            .where(Task.column_id == column_id)
            .order_by(Task.position.asc())
            .with_for_update()
        )
        tasks = (await session.execute(stmt)).scalars().all()

        for index, task in enumerate(tasks):
            task.position = (index + 1) * POSITION_GAP
            session.add(task)

        await session.flush()
