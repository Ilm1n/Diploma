from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db.database import db_helper
from src.users.models import User
from src.auth.dependencies import get_current_user
from src.projects.models import ProjectMember
from src.boards.models import Task, BoardColumn


async def validate_project_member(
    project_id: int,
    user: User,
    session: AsyncSession,
) -> None:
    """
    Проверяет, состоит ли пользователь в проекте.
    """
    query = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
    )
    result = await session.execute(query)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )


async def get_valid_task(
    task_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
) -> Task:
    """
    Получает задачу по ID и проверяет доступ пользователя к проекту этой задачи.
    """
    query = select(Task).where(Task.id == task_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    await validate_project_member(task.project_id, current_user, session)

    return task


async def get_valid_column(
    column_id: int = Path(...),
    session: AsyncSession = Depends(db_helper.get_async_session),
) -> BoardColumn:
    query = select(BoardColumn).where(BoardColumn.id == column_id)
    result = await session.execute(query)
    column = result.scalar_one_or_none()

    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
        )
    return column
