from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import db_helper
from src.users.models import User
from src.auth.dependencies import get_current_user
from src.boards.schemas import ColumnCreate, ColumnRead, TaskCreate, TaskRead, TaskMove
from src.boards import service, dependencies
from src.boards.models import Task, BoardColumn

router = APIRouter(tags=["Boards"])


@router.get("/projects/{project_id}/columns", response_model=list[ColumnRead])
async def get_project_board(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    await dependencies.validate_project_member(project_id, current_user, session)
    return await service.BoardService.get_board(session, project_id)


@router.post(
    "/projects/{project_id}/columns",
    response_model=ColumnRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_column(
    project_id: int,
    column_in: ColumnCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    await dependencies.validate_project_member(project_id, current_user, session)
    return await service.BoardService.create_column(session, project_id, column_in)


@router.post(
    "/projects/{project_id}/columns/{column_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    await dependencies.validate_project_member(project_id, current_user, session)

    if column.project_id != project_id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail="Column does not belong to this project"
        )

    return await service.BoardService.create_task(
        session, project_id, column.id, task_in, current_user.id
    )


@router.patch("/tasks/{task_id}/move", response_model=TaskRead)
async def move_task(
    move_data: TaskMove,
    task: Annotated[Task, Depends(dependencies.get_valid_task)],
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    return await service.BoardService.move_task(session, task, move_data)
