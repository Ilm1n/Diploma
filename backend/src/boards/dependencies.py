from typing import Annotated

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
) -> ProjectMember:
    query = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
    )
    result = await session.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )
    return member


async def get_valid_task(
    task_id: Annotated[int, Path(...)],
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
) -> Task:
    query = select(Task).where(Task.id == task_id)
    result = await session.execute(query)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    await validate_project_member(task.project_id, user, session)

    return task


async def get_valid_column(
    column_id: Annotated[int, Path(...)],
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
