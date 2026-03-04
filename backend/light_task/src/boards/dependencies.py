from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.boards.models import BoardColumn, Task
from src.db.database import db_helper
from src.projects.constants import ProjectRole
from src.messages import MESSAGES
from src.projects.models import ProjectMember


async def get_valid_column(
    project_id: Annotated[int, Path(...)],
    column_id: Annotated[int, Path(...)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> BoardColumn:
    query = (
        select(BoardColumn)
        .where(
            BoardColumn.id == column_id,
            BoardColumn.project_id == project_id,
        )
        .options(selectinload(BoardColumn.tasks).selectinload(Task.tags))
    )
    column = (await session.execute(query)).scalar_one_or_none()

    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MESSAGES["COLUMN_NOT_FOUND"],
        )
    return column


class TaskAccessChecker:
    def __init__(
        self,
        required_roles: list[ProjectRole] | None = None,
        check_assignee: bool = False,
    ):
        self.required_roles = required_roles or []
        self.check_assignee = check_assignee

    async def __call__(
        self,
        task_id: Annotated[int, Path(...)],
        user: Annotated[UserPayload, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    ) -> Task:
        query = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.tags),
            )
        )
        result = await session.execute(query)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MESSAGES["TASK_NOT_FOUND"],
            )

        query = select(ProjectMember).where(
            ProjectMember.project_id == task.project_id,
            ProjectMember.user_id == user.sub,
        )
        member = (await session.execute(query)).scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MESSAGES["INSUFFICIENT_PERMISSIONS"],
            )

        if member.role in [ProjectRole.OWNER, ProjectRole.MANAGER]:
            return task

        if self.required_roles and member.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MESSAGES["INSUFFICIENT_PERMISSIONS"],
            )

        if self.check_assignee and member.role == ProjectRole.MEMBER:
            if task.assignee_id != user.sub:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=MESSAGES["MEMBERS_ONLY_OWN_TASKS"],
                )

        return task


get_task_for_read = TaskAccessChecker()
get_task_for_delete = TaskAccessChecker(
    required_roles=[ProjectRole.OWNER, ProjectRole.MANAGER]
)
get_task_for_update = TaskAccessChecker(check_assignee=True)
