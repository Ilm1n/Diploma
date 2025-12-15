from datetime import datetime

from pydantic import Field

from src.core.schemas import BaseSchema
from src.projects.constants import ProjectRole


class ProjectBase(BaseSchema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime


class ProjectMemberBase(BaseSchema):
    user_id: int
    role: ProjectRole


class ProjectMemberRead(ProjectMemberBase):
    id: int
    joined_at: datetime
