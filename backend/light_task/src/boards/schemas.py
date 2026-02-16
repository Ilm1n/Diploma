from datetime import datetime

from pydantic import Field

from src.boards.constants import TaskPriority
from src.schemas import BaseSchema
from src.tags.schemas import TagRead


class TaskBase(BaseSchema):
    title: str = Field(min_length=1, max_length=200)
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: int | None = None


class TaskCreate(TaskBase):
    description: str | None
    tag_ids: list[int] = Field(default_factory=list)


class TaskUpdate(BaseSchema):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    tag_ids: list[int] | None = None


class TaskMove(BaseSchema):
    new_column_id: int
    after_task_id: int | None = None


class TaskPreview(TaskBase):
    id: int
    column_id: int
    project_id: int
    position: float
    tags: list[TagRead] = Field(default_factory=list)


class TaskRead(TaskPreview):
    description: str | None
    author_id: int | None
    created_at: datetime
    updated_at: datetime

class TaskMoveResponse(BaseSchema):
    id: int
    column_id: int
    position: float
    updated_at: datetime


class ColumnBase(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    tasks_limit: int | None = Field(None, gt=0)


class ColumnCreate(ColumnBase):
    pass


class ColumnUpdate(BaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    tasks_limit: int | None = Field(None, gt=0)


class ColumnReorderRequest(BaseSchema):
    column_ids: list[int]


class ColumnRead(ColumnBase):
    id: int
    project_id: int
    position: float
    tasks_limit: int | None
    tasks: list[TaskPreview] = Field(default_factory=list)
