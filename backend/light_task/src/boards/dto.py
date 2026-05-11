from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.boards.constants import TaskPriority


@dataclass(frozen=True, kw_only=True)
class CreateTaskCommand:
    project_id: int
    column_id: int
    author_id: int
    title: str
    description: str | None
    priority: TaskPriority | None
    assignee_id: int | None
    deadline_at: datetime | None
    tag_ids: list[int] = field(default_factory=list)
    client_mutation_id: str | None = None
