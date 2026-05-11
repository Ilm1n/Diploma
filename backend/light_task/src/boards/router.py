from typing import Annotated

from fastapi import APIRouter, Depends, status, Query

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.boards import dependencies
from src.boards.dto import CreateTaskCommand, MoveTaskCommand
from src.boards.events import BoardsDomainEventDispatcher
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
    TaskMoveResponse,
    TaskPreview,
)
from src.boards.service import BoardService, get_board_service
from src.boards.use_cases import CreateTaskUseCase, MoveTaskUseCase
from src.db.database import db_helper
from src.db.unit_of_work import UnitOfWork
from src.realtimev1.dependencies import get_client_mutation_id, get_event_publisher
from src.realtimev1.publisher import DomainEventPublisher

from src.projects.dependencies import (
    check_project_member,
    check_project_manager,
)

router = APIRouter(tags=["Boards"])


def get_create_task_use_case(
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> CreateTaskUseCase:
    dispatcher = BoardsDomainEventDispatcher(
        db_helper.async_session_maker,
        event_publisher,
    )
    return CreateTaskUseCase(lambda: UnitOfWork(event_dispatcher=dispatcher))


def get_move_task_use_case(
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> MoveTaskUseCase:
    dispatcher = BoardsDomainEventDispatcher(
        db_helper.async_session_maker,
        event_publisher,
    )
    return MoveTaskUseCase(lambda: UnitOfWork(event_dispatcher=dispatcher))


@router.get("/projects/{project_id}/columns", response_model=list[ColumnRead])
async def get_project_board(
    project_id: int,
    _: Annotated[None, Depends(check_project_member)],
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
    _: Annotated[None, Depends(check_project_manager)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    return await board_service.create_column(
        project_id,
        column_in,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.patch(
    "/projects/{project_id}/columns/{column_id}",
    response_model=ColumnRead,
)
async def update_column(
    column_update: ColumnUpdate,
    _: Annotated[None, Depends(check_project_manager)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    return await board_service.update_column(
        column,
        column_update,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.delete(
    "/projects/{project_id}/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_column(
    _: Annotated[None, Depends(check_project_manager)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    column: Annotated[BoardColumn, Depends(dependencies.get_valid_column)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    await board_service.delete_column(
        column,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.post(
    "/projects/{project_id}/columns/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reorder_columns(
    project_id: int,
    reorder_data: ColumnReorderRequest,
    _: Annotated[None, Depends(check_project_manager)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    await board_service.reorder_columns(
        project_id,
        reorder_data,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.post(
    "/projects/{project_id}/columns/{column_id}/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    column_id: int,
    task_in: TaskCreate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    _: Annotated[None, Depends(check_project_member)],
    use_case: Annotated[CreateTaskUseCase, Depends(get_create_task_use_case)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    command = CreateTaskCommand(
        project_id=project_id,
        author_id=current_user.sub,
        column_id=column_id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        assignee_id=task_in.assignee_id,
        deadline_at=task_in.deadline_at,
        tag_ids=task_in.tag_ids,
        client_mutation_id=client_mutation_id,
    )
    return await use_case.execute(command)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskPreview])
async def get_project_tasks(
    project_id: int,
    _: Annotated[None, Depends(check_project_member)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    assignee_id: Annotated[int | None, Query()] = None,
    tag_ids: Annotated[list[int] | None, Query()] = None,
    search: Annotated[str | None, Query(min_length=3)] = None,
):
    return await board_service.get_project_tasks(
        project_id=project_id, assignee_id=assignee_id, tag_ids=tag_ids, search=search
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task_details(
    task: Annotated[Task, Depends(dependencies.get_task_for_read)],
):
    return task


@router.patch("/tasks/{task_id}/move", response_model=TaskMoveResponse)
async def move_task(
    task_id: int,
    move_data: TaskMove,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    use_case: Annotated[MoveTaskUseCase, Depends(get_move_task_use_case)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    command = MoveTaskCommand(
        task_id=task_id,
        actor_user_id=current_user.sub,
        new_column_id=move_data.new_column_id,
        after_task_id=move_data.after_task_id,
        client_mutation_id=client_mutation_id,
    )
    return await use_case.execute(command)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
async def update_task(
    task_update: TaskUpdate,
    task: Annotated[Task, Depends(dependencies.get_task_for_update)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    return await board_service.update_task(
        task,
        task_update,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Annotated[Task, Depends(dependencies.get_task_for_delete)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    await board_service.delete_task(
        task,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )
