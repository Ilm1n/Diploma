from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.boards import dependencies
from src.boards.models import BoardColumn, Task
from src.boards.schemas import (
    ColumnCreate,
    ColumnRead,
    TaskCreate,
    TaskMove,
    TaskRead,
    TaskUpdate,
    ColumnUpdate,
    ColumnReorderRequest,
)
from src.boards.service import BoardService
from src.core.db.database import db_helper

from src.projects.dependencies import (
    require_project_member,
    require_project_manager,
)
from src.projects.models import Project
from src.users.models import User

router = APIRouter(tags=["Boards"])


@router.get("/projects/{project_id}/columns", response_model=list[ColumnRead])
async def get_project_board(
    project_id: int,
    _: Annotated[Project, Depends(require_project_member)],
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
    _: Annotated[Project, Depends(require_project_manager)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.create_column(session, project_id, column_in)


@router.patch(
    "/projects/{project_id}/columns/{column_id}",
    response_model=ColumnRead,
)
async def update_column(
    project_id: int,
    column_id: int,
    column_update: ColumnUpdate,
    _: Annotated[Project, Depends(require_project_manager)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.update_column(session, column, column_update)


@router.delete(
    "/projects/{project_id}/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_column(
    project_id: int,
    column_id: int,
    _: Annotated[Project, Depends(require_project_manager)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await BoardService.delete_column(session, column)


@router.post(
    "/projects/{project_id}/columns/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reorder_columns(
    project_id: int,
    reorder_data: ColumnReorderRequest,
    _: Annotated[Project, Depends(require_project_manager)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await BoardService.reorder_columns(session, project_id, reorder_data)


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
    _: Annotated[Project, Depends(require_project_manager)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.create_task(
        session, project_id, column.id, task_in, current_user.id
    )


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def get_project_tasks(
    project_id: int,
    _: Annotated[Project, Depends(require_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    assignee_id: Annotated[int | None, Query()] = None,
    tag_ids: Annotated[list[int] | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=3)] = None,
):
    return await BoardService.get_project_tasks(
        session, project_id, assignee_id=assignee_id, tag_ids=tag_ids, search=search
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task_details(
    task: Annotated[Task, Depends(dependencies.get_task_for_read)],
):
    return task


@router.patch("/tasks/{task_id}/move", response_model=TaskRead)
async def move_task(
    move_data: TaskMove,
    task: Annotated[Task, Depends(dependencies.get_task_for_update)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.move_task(session, task, move_data)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_update: TaskUpdate,
    task: Annotated[Task, Depends(dependencies.get_task_for_update)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await BoardService.update_task(session, task, task_update)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Annotated[Task, Depends(dependencies.get_task_for_delete)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await BoardService.delete_task(session, task)
