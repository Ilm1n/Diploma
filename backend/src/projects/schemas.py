from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberBase(BaseModel):
    user_id: int
    role: str


class ProjectMemberRead(ProjectMemberBase):
    id: int
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)

