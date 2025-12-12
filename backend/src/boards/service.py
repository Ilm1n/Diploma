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
        query = (
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(BoardColumn.position.asc())
            .options(selectinload(BoardColumn.tasks))
        )
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_column(
        session: AsyncSession, project_id: int, data: ColumnCreate
    ) -> BoardColumn:
        query = select(func.max(BoardColumn.position)).where(
            BoardColumn.project_id == project_id
        )
        result = await session.execute(query)
        max_pos = result.scalar() or 0.0

        new_column = BoardColumn(
            name=data.name,
            project_id=project_id,
            position=max_pos + POSITION_GAP,
        )
        session.add(new_column)
        await session.commit()
        await session.refresh(new_column)
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
        col_exists = await session.execute(
            select(BoardColumn.id).where(
                BoardColumn.id == column_id, BoardColumn.project_id == project_id
            )
        )
        if not col_exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Column not found in this project",
            )

        if data.assignee_id is not None:
            member_check = await session.execute(
                select(ProjectMember.id).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == data.assignee_id,
                )
            )
            if not member_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Assignee with id {data.assignee_id} is not a member of this project or does not exist.",
                )

        query = select(func.max(Task.position)).where(Task.column_id == column_id)
        result = await session.execute(query)
        max_pos = result.scalar() or 0.0

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
                    detail="Invalid target column",
                )

        attempts = 0
        while attempts < 2:
            attempts += 1
            new_position = await BoardService._calculate_position(
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
            detail="Could not determine task position after rebalancing.",
        )

    @staticmethod
    async def _calculate_position(
        session: AsyncSession, column_id: int, after_task_id: Optional[int]
    ) -> Optional[float]:
        if after_task_id is None:
            stmt = (
                select(Task)
                .where(Task.column_id == column_id)
                .order_by(Task.position.asc())
                .limit(1)
                .with_for_update()
            )
            first_task = (await session.execute(stmt)).scalar_one_or_none()

            if not first_task:
                return POSITION_GAP

            new_pos = first_task.position / 2.0
            if new_pos < MIN_POSITION_DELTA:
                return None
            return new_pos

        else:
            prev_task = await session.get(Task, after_task_id, with_for_update=True)

            if not prev_task or prev_task.column_id != column_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Target 'after_task' not found in target column.",
                )

            stmt = (
                select(Task)
                .where(
                    Task.column_id == column_id,
                    Task.position > prev_task.position,
                )
                .order_by(Task.position.asc())
                .limit(1)
                .with_for_update()
            )
            next_task = (await session.execute(stmt)).scalar_one_or_none()

            if not next_task:
                return prev_task.position + POSITION_GAP

            delta = next_task.position - prev_task.position
            if delta < MIN_POSITION_DELTA:
                return None

            return prev_task.position + (delta / 2.0)

    @staticmethod
    async def _rebalance_column(session: AsyncSession, column_id: int):
        stmt = (
            select(Task)
            .where(Task.column_id == column_id)
            .order_by(Task.position.asc())
            .with_for_update()
        )
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        for index, task in enumerate(tasks):
            task.position = (index + 1) * POSITION_GAP
            session.add(task)

        await session.flush()
