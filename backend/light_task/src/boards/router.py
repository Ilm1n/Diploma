from typing import Annotated

from fastapi import APIRouter, Depends, status, Query

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
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
    TaskMoveResponse, TaskPreview,
)
from src.boards.service import BoardService, get_board_service

from src.projects.dependencies import (
    require_project_member,
    require_project_manager,
)
from src.projects.models import Project

router = APIRouter(tags=["Boards"])


@router.get("/projects/{project_id}/columns", response_model=list[ColumnRead])
async def get_project_board(
    project_id: int,
    _: Annotated[Project, Depends(require_project_member)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    return await board_service.get_board(project_id)


@router.post(
    "/projects/{project_id}/columns",
    response_model=ColumnRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_column(
    project_id: int,
    column_in: ColumnCreate,
    _: Annotated[Project, Depends(require_project_manager)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    return await board_service.create_column(project_id, column_in)


@router.patch(
    "/projects/{project_id}/columns/{column_id}",
    response_model=ColumnRead,
)
async def update_column(
    column_update: ColumnUpdate,
    _: Annotated[Project, Depends(require_project_manager)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    return await board_service.update_column(column, column_update)


@router.delete(
    "/projects/{project_id}/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_column(
    _: Annotated[Project, Depends(require_project_manager)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    await board_service.delete_column(column)


@router.post(
    "/projects/{project_id}/columns/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reorder_columns(
    project_id: int,
    reorder_data: ColumnReorderRequest,
    _: Annotated[Project, Depends(require_project_manager)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    await board_service.reorder_columns(project_id, reorder_data)


@router.post(
    "/projects/{project_id}/columns/{column_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    task_in: TaskCreate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    _: Annotated[Project, Depends(require_project_manager)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    return await board_service.create_task(
        project_id=project_id,
        column_id=column.id,
        data=task_in,
        author_id=current_user.sub
    )


@router.get("/projects/{project_id}/tasks", response_model=list[TaskPreview])
async def get_project_tasks(
    project_id: int,
    _: Annotated[Project, Depends(require_project_member)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    assignee_id: Annotated[int | None, Query()] = None,
    tag_ids: Annotated[list[int] | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=3)] = None,
):
    return await board_service.get_project_tasks(
        project_id=project_id,
        assignee_id=assignee_id,
        tag_ids=tag_ids,
        search=search
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task_details(
    task: Annotated[Task, Depends(dependencies.get_task_for_read)],
):
    return task


@router.patch("/tasks/{task_id}/move", response_model=TaskMoveResponse)
async def move_task(
    move_data: TaskMove,
    task: Annotated[Task, Depends(dependencies.get_task_for_update)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    return await board_service.move_task(task, move_data)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_update: TaskUpdate,
    task: Annotated[Task, Depends(dependencies.get_task_for_update)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    return await board_service.update_task(task, task_update)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Annotated[Task, Depends(dependencies.get_task_for_delete)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
):
    await board_service.delete_task(task)