from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.boards import dependencies
from src.boards.models import BoardColumn, Task
from src.boards.schemas import ColumnCreate, ColumnRead, TaskCreate, TaskMove, TaskRead
from src.boards.service import BoardService
from src.core.db.database import db_helper
from src.projects.dependencies import get_project_member
from src.projects.models import ProjectMember
from src.users.models import User

router = APIRouter(tags=["Boards"])


@router.get("/projects/{project_id}/columns", response_model=list[ColumnRead])
async def get_project_board(
    project_id: int,
    _: Annotated[ProjectMember, Depends(get_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.get_board(session, project_id)


@router.post(
    "/projects/{project_id}/columns",
    response_model=ColumnRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_column(
    project_id: int,
    column_in: ColumnCreate,
    _: Annotated[ProjectMember, Depends(get_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.create_column(session, project_id, column_in)


@router.post(
    "/projects/{project_id}/columns/{column_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    _: Annotated[ProjectMember, Depends(get_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.create_task(
        session, project_id, column.id, task_in, current_user.id
    )


@router.patch("/tasks/{task_id}/move", response_model=TaskRead)
async def move_task(
    move_data: TaskMove,
    task: Annotated[Task, Depends(dependencies.get_valid_task)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.move_task(session, task, move_data)
