from datetime import datetime
from pydantic import Field

from src.boards.constants import TaskPriority
from src.core.schemas import BaseSchema


class TaskBase(BaseSchema):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseSchema):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    priority: TaskPriority | None = None
    assignee_id: int | None = None


class TaskMove(BaseSchema):
    new_column_id: int
    after_task_id: int | None = None


class TaskRead(TaskBase):
    id: int
    column_id: int
    project_id: int
    author_id: int | None
    position: float
    created_at: datetime
    updated_at: datetime


class ColumnBase(BaseSchema):
    name: str = Field(min_length=1, max_length=100)


class ColumnCreate(ColumnBase):
    pass


class ColumnUpdate(BaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)


class ColumnRead(ColumnBase):
    id: int
    project_id: int
    position: float
    tasks: list[TaskRead] = Field(default_factory=list)
