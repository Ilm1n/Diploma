from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from src.boards.constants import TaskPriority


class TaskBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None


class TaskMove(BaseModel):
    new_column_id: int
    new_position: float


class TaskRead(TaskBase):
    id: int
    column_id: int
    project_id: int
    author_id: int | None
    position: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ColumnBase(BaseModel):
    name: str = Field(..., max_length=100)


class ColumnCreate(ColumnBase):
    pass


class ColumnUpdate(ColumnBase):
    name: str | None = None


class ColumnRead(ColumnBase):
    id: int
    project_id: int
    position: float
    tasks: list[TaskRead] = []

    model_config = ConfigDict(from_attributes=True)
