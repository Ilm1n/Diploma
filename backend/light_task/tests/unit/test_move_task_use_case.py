from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.boards.dto import MoveTaskCommand
from src.boards.events import TaskMoved
from src.boards.ordering import POSITION_GAP, TaskOrdering
from src.boards.repository import BoardRepository
from src.boards.use_cases import MoveTaskUseCase
from src.projects.constants import ProjectRole
from src.shared.errors import ConflictError


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.execute_count = 0
        self.commit_count = 0

    def add(self, instance: object) -> None:
        self.added.append(instance)

    async def execute(self, statement):
        self.execute_count += 1
        return None

    async def commit(self) -> None:
        self.commit_count += 1


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = object()
        self.events: list[object] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        return False

    def collect_event(self, event: object) -> None:
        self.events.append(event)


class FakeMoveTaskRepository:
    def __init__(self, session: object) -> None:
        self.task = SimpleNamespace(
            id=123,
            project_id=1,
            column_id=2,
            assignee_id=None,
            position=POSITION_GAP,
        )

    async def get_task_for_update(self, task_id: int):
        return self.task

    async def get_project_member(self, *, project_id: int, user_id: int):
        return SimpleNamespace(role=ProjectRole.OWNER)

    async def get_column(self, column_id: int):
        return SimpleNamespace(id=column_id, project_id=1, tasks_limit=None)

    async def count_tasks_in_column(self, column_id: int) -> int:
        return 0

    async def get_first_task_position_for_update(self, column_id: int):
        return None

    async def get_anchor_task_position_for_update(
        self,
        *,
        column_id: int,
        after_task_id: int,
    ):
        return None

    async def get_next_task_position_for_update(
        self,
        *,
        column_id: int,
        anchor_position: float,
    ):
        return None

    async def list_column_tasks_for_update(self, column_id: int):
        return []

    def save_task(self, task) -> None:
        self.task = task

    async def touch_project(self, project_id: int) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def get_task_with_tags(self, task_id: int):
        return self.task


class FakeOrderingRepository:
    def __init__(
        self,
        *,
        first_position: float | None = None,
        anchor_position: float | None = None,
        next_position: float | None = None,
    ) -> None:
        self.first_position = first_position
        self.anchor_position = anchor_position
        self.next_position = next_position
        self.tasks = [
            SimpleNamespace(position=9.0),
            SimpleNamespace(position=10.0),
        ]
        self.flush_count = 0

    async def get_first_task_position_for_update(self, column_id: int):
        return self.first_position

    async def get_anchor_task_position_for_update(
        self,
        *,
        column_id: int,
        after_task_id: int,
    ):
        return self.anchor_position

    async def get_next_task_position_for_update(
        self,
        *,
        column_id: int,
        anchor_position: float,
    ):
        return self.next_position

    async def list_column_tasks_for_update(self, column_id: int):
        return self.tasks

    async def flush(self) -> None:
        self.flush_count += 1


@pytest.mark.asyncio
async def test_move_repository_methods_do_not_commit() -> None:
    session = FakeSession()
    repository = BoardRepository(session)  # type: ignore[arg-type]
    task = SimpleNamespace(id=1)

    repository.save_task(task)  # type: ignore[arg-type]
    await repository.touch_project(1)

    assert session.added == [task]
    assert session.execute_count == 1
    assert session.commit_count == 0


@pytest.mark.asyncio
async def test_move_task_use_case_registers_task_moved_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow = FakeUnitOfWork()
    monkeypatch.setattr("src.boards.use_cases.BoardRepository", FakeMoveTaskRepository)
    use_case = MoveTaskUseCase(lambda: uow)  # type: ignore[arg-type]

    result = await use_case.execute(
        MoveTaskCommand(
            task_id=123,
            actor_user_id=7,
            new_column_id=3,
            after_task_id=None,
            client_mutation_id="mutation-1",
        )
    )

    assert result.id == 123
    assert result.column_id == 3
    assert len(uow.events) == 1
    event = uow.events[0]
    assert isinstance(event, TaskMoved)
    assert event.task_id == 123
    assert event.from_column_id == 2
    assert event.to_column_id == 3
    assert event.actor_user_id == 7
    assert event.project_id == 1
    assert event.client_mutation_id == "mutation-1"


@pytest.mark.asyncio
async def test_task_ordering_raises_for_missing_anchor() -> None:
    ordering = TaskOrdering(FakeOrderingRepository(anchor_position=None))

    with pytest.raises(ConflictError) as exc_info:
        await ordering.calculate_new_position(column_id=1, after_task_id=999)

    assert str(exc_info.value.code) == "ANCHOR_TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_task_ordering_rebalances_column_positions() -> None:
    repository = FakeOrderingRepository()
    ordering = TaskOrdering(repository)

    await ordering.rebalance_column(1)

    assert [task.position for task in repository.tasks] == [
        POSITION_GAP,
        POSITION_GAP * 2,
    ]
    assert repository.flush_count == 1
