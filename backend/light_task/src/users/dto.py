from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class RegisterUserCommand:
    username: str
    email: str
    password: str


@dataclass(frozen=True, kw_only=True)
class GetUserQuery:
    user_id: int


@dataclass(frozen=True, kw_only=True)
class UpdateUserCommand:
    user_id: int
    changes: dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class UpdateUserPasswordCommand:
    user_id: int
    current_password: str | None
    new_password: str
