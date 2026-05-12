from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.users.dto import (
    RegisterUserCommand,
    UpdateUserCommand,
    UpdateUserPasswordCommand,
)
from src.users.repository import UserRepository
from src.users.use_cases import (
    RegisterUserUseCase,
    UpdateUserPasswordUseCase,
    UpdateUserUseCase,
)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commit_count = 0
        self.flush_count = 0
        self.refresh_count = 0

    def add(self, instance: object) -> None:
        self.added.append(instance)

    async def get(self, model, ident: int):
        return None

    async def commit(self) -> None:
        self.commit_count += 1

    async def flush(self) -> None:
        self.flush_count += 1

    async def refresh(self, instance: object) -> None:
        self.refresh_count += 1


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = object()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        return False


class FakeUserRepository:
    def __init__(self, session: object) -> None:
        self.user = SimpleNamespace(
            id=1,
            username="user",
            email="user@example.com",
            hashed_password=None,
            full_name=None,
            avatar_url=None,
            is_active=True,
        )

    def add_user(self, **kwargs):
        self.user.username = kwargs["username"]
        self.user.email = kwargs["email"]
        self.user.hashed_password = kwargs["hashed_password"]
        return self.user

    async def get_user(self, user_id: int):
        self.user.id = user_id
        return self.user

    def save_user(self, user: object) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def refresh_user(self, user: object) -> None:
        return None


@pytest.mark.asyncio
async def test_user_repository_methods_do_not_commit() -> None:
    session = FakeSession()
    repository = UserRepository(session)  # type: ignore[arg-type]
    user = SimpleNamespace(id=1)

    repository.add_user(
        email="user@example.com",
        username="user",
        hashed_password="hash",
    )
    repository.save_user(user)  # type: ignore[arg-type]
    await repository.flush()
    await repository.refresh_user(user)  # type: ignore[arg-type]

    assert session.added
    assert session.flush_count == 1
    assert session.refresh_count == 1
    assert session.commit_count == 0


@pytest.mark.asyncio
async def test_register_user_use_case_hashes_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow = FakeUnitOfWork()
    monkeypatch.setattr("src.users.use_cases.UserRepository", FakeUserRepository)
    monkeypatch.setattr(
        "src.users.use_cases.hash_password", lambda value: f"hashed:{value}"
    )
    use_case = RegisterUserUseCase(lambda: uow)  # type: ignore[arg-type]

    result = await use_case.execute(
        RegisterUserCommand(
            username="user",
            email="user@example.com",
            password="password",
        )
    )

    assert result.hashed_password == "hashed:password"


@pytest.mark.asyncio
async def test_update_user_use_case_applies_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow = FakeUnitOfWork()
    monkeypatch.setattr("src.users.use_cases.UserRepository", FakeUserRepository)
    use_case = UpdateUserUseCase(lambda: uow)  # type: ignore[arg-type]

    result = await use_case.execute(
        UpdateUserCommand(
            user_id=1,
            changes={"username": "renamed", "full_name": "Ada"},
        )
    )

    assert result.username == "renamed"
    assert result.full_name == "Ada"


@pytest.mark.asyncio
async def test_update_password_use_case_hashes_new_password_for_passwordless_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow = FakeUnitOfWork()
    monkeypatch.setattr("src.users.use_cases.UserRepository", FakeUserRepository)
    monkeypatch.setattr(
        "src.users.use_cases.hash_password", lambda value: f"hashed:{value}"
    )
    use_case = UpdateUserPasswordUseCase(lambda: uow)  # type: ignore[arg-type]

    result = await use_case.execute(
        UpdateUserPasswordCommand(
            user_id=1,
            current_password=None,
            new_password="new-password",
        )
    )

    assert result.hashed_password == "hashed:new-password"
