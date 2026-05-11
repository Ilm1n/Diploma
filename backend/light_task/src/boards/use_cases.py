from __future__ import annotations

from collections.abc import Callable

from src.boards.dto import CreateTaskCommand
from src.boards.events import TaskCreated
from src.boards.models import Task
from src.boards.permissions import BoardPermissions
from src.boards.repository import BoardRepository
from src.db.unit_of_work import UnitOfWork
from src.errors import ErrorCode
from src.logger import board_logger
from src.shared.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    DatabaseError,
    NotFoundError,
)


POSITION_GAP = 65536.0


class CreateTaskUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        permissions: BoardPermissions | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._permissions = permissions or BoardPermissions()

    async def execute(self, command: CreateTaskCommand) -> Task:
        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("UnitOfWork has not been entered")

                repository = BoardRepository(uow.session)
                column = await repository.get_column(command.column_id)
                if column is None:
                    raise NotFoundError(ErrorCode.COLUMN_NOT_FOUND)

                if column.project_id != command.project_id:
                    raise BadRequestError(ErrorCode.COLUMN_BELONGS_ANOTHER_PROJECT)

                if column.tasks_limit is not None:
                    current_count = await repository.count_tasks_in_column(
                        command.column_id
                    )
                    if current_count >= column.tasks_limit:
                        raise ConflictError(ErrorCode.COLUMN_TASK_LIMIT_REACHED)

                actor_member = await repository.get_project_member(
                    project_id=command.project_id,
                    user_id=command.author_id,
                )
                self._permissions.ensure_task_assignee_allowed(
                    actor_member=actor_member,
                    actor_user_id=command.author_id,
                    assignee_id=command.assignee_id,
                )

                if command.assignee_id is not None:
                    assignee_exists = await repository.project_member_exists(
                        project_id=command.project_id,
                        user_id=command.assignee_id,
                    )
                    if not assignee_exists:
                        raise BadRequestError(ErrorCode.ASSIGNEE_NOT_PROJECT_MEMBER)

                tags = await repository.list_tags_by_ids(
                    project_id=command.project_id,
                    tag_ids=command.tag_ids,
                )
                if len(tags) != len(command.tag_ids):
                    raise BadRequestError(ErrorCode.INVALID_TAG_IDS)

                max_position = await repository.get_max_task_position(command.column_id)
                task = await repository.add_task(
                    title=command.title,
                    description=command.description,
                    priority=command.priority,
                    deadline_at=command.deadline_at,
                    project_id=command.project_id,
                    column_id=command.column_id,
                    assignee_id=command.assignee_id,
                    author_id=command.author_id,
                    position=max_position + POSITION_GAP,
                    tags=tags,
                )
                await repository.touch_project(command.project_id)
                await repository.flush()

                loaded_task = await repository.get_task_with_tags(task.id)
                if loaded_task is None:
                    raise DatabaseError()

                uow.collect_event(
                    TaskCreated(
                        task_id=loaded_task.id,
                        actor_user_id=command.author_id,
                        project_id=command.project_id,
                        client_mutation_id=command.client_mutation_id,
                    )
                )
                return loaded_task
        except AppError:
            raise
        except Exception as exc:
            board_logger.exception(
                "Failed to create task in project %s",
                command.project_id,
                exc_info=exc,
            )
            raise DatabaseError() from exc
