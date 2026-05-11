from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from src.db.unit_of_work import UnitOfWork
from src.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class SampleEvent(DomainEvent):
    name: str


class FakeSession:
    def __init__(self, commit_error: Exception | None = None) -> None:
        self.commit_error = commit_error
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    async def commit(self) -> None:
        self.commit_count += 1
        if self.commit_error:
            raise self.commit_error

    async def rollback(self) -> None:
        self.rollback_count += 1

    async def close(self) -> None:
        self.close_count += 1


class RecordingDispatcher:
    def __init__(self) -> None:
        self.dispatched: list[tuple[DomainEvent, ...]] = []

    async def dispatch(self, events: Sequence[DomainEvent]) -> None:
        self.dispatched.append(tuple(events))


@pytest.mark.asyncio
async def test_unit_of_work_commits_once_and_dispatches_events_after_commit() -> None:
    session = FakeSession()
    dispatcher = RecordingDispatcher()
    event = SampleEvent(name="created")

    async with UnitOfWork(lambda: session, dispatcher) as uow:
        uow.collect_event(event)
        assert session.commit_count == 0
        assert dispatcher.dispatched == []

    assert session.commit_count == 1
    assert session.rollback_count == 0
    assert session.close_count == 1
    assert dispatcher.dispatched == [(event,)]


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_on_exception() -> None:
    session = FakeSession()
    dispatcher = RecordingDispatcher()

    with pytest.raises(RuntimeError):
        async with UnitOfWork(lambda: session, dispatcher) as uow:
            uow.collect_event(SampleEvent(name="created"))
            raise RuntimeError("boom")

    assert session.commit_count == 0
    assert session.rollback_count == 1
    assert session.close_count == 1
    assert dispatcher.dispatched == []


@pytest.mark.asyncio
async def test_unit_of_work_does_not_dispatch_events_after_commit_failure() -> None:
    session = FakeSession(commit_error=RuntimeError("commit failed"))
    dispatcher = RecordingDispatcher()

    with pytest.raises(RuntimeError, match="commit failed"):
        async with UnitOfWork(lambda: session, dispatcher) as uow:
            uow.collect_event(SampleEvent(name="created"))

    assert session.commit_count == 1
    assert session.rollback_count == 1
    assert session.close_count == 1
    assert dispatcher.dispatched == []


@pytest.mark.asyncio
async def test_unit_of_work_manual_commit_dispatches_events_once() -> None:
    session = FakeSession()
    dispatcher = RecordingDispatcher()
    event = SampleEvent(name="created")

    async with UnitOfWork(lambda: session, dispatcher) as uow:
        uow.collect_event(event)
        await uow.commit()

    assert session.commit_count == 1
    assert session.rollback_count == 0
    assert session.close_count == 1
    assert dispatcher.dispatched == [(event,)]
