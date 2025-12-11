from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.boards.models import BoardColumn, Task
from src.boards.schemas import ColumnCreate, TaskCreate, TaskMove


class BoardService:
    @staticmethod
    async def get_board(session: AsyncSession, project_id: int) -> list[BoardColumn]:
        query = (
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(BoardColumn.position)
            .options(selectinload(BoardColumn.tasks))
        )
        result = await session.execute(query)
        return list(result.scalars().all())

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
            name=data.name, project_id=project_id, position=max_pos + 1000.0
        )
        session.add(new_column)
        await session.commit()
        await session.refresh(new_column)
        return new_column

    @staticmethod
    async def create_task(
        session: AsyncSession,
        project_id: int,
        column_id: int,
        data: TaskCreate,
        author_id: int,
    ) -> Task:
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
            position=max_pos + 1000.0,
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        return new_task

    @staticmethod
    async def move_task(session: AsyncSession, task: Task, data: TaskMove) -> Task:
        task.column_id = data.new_column_id
        task.position = data.new_position

        await session.commit()
        await session.refresh(task)
        return task
