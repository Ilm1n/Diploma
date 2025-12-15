from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.boards.models import BoardColumn, Task
from src.core.db.database import db_helper
from src.projects.models import ProjectMember
from src.users.models import User


async def get_valid_column(
    project_id: Annotated[int, Path(...)],
    column_id: Annotated[int, Path(...)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> BoardColumn:
    query = select(BoardColumn).where(
        BoardColumn.id == column_id,
        BoardColumn.project_id == project_id,
    )
    column = (await session.execute(query)).scalar_one_or_none()

    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found or does not belong to this project",
        )
    return column


async def get_valid_task(
    task_id: Annotated[int, Path(...)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> Task:
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    query = select(ProjectMember).where(
        ProjectMember.project_id == task.project_id,
        ProjectMember.user_id == user.id,
    )
    member = (await session.execute(query)).scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to the project of this task",
        )

    return task
