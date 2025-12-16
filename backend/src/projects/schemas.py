from datetime import datetime

from pydantic import Field

from src.core.schemas import BaseSchema
from src.projects.constants import ProjectRole
from src.users.schemas import UserPublic


class ProjectBase(BaseSchema):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseSchema):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    current_user_role: ProjectRole | None = None


class ProjectMemberRead(BaseSchema):
    id: int
    user: UserPublic
    role: ProjectRole
    joined_at: datetime


class ProjectMemberUpdate(BaseSchema):
    role: ProjectRole
