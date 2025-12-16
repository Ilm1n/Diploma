from datetime import datetime
from pydantic import EmailStr
from src.core.schemas import BaseSchema
from src.projects.constants import ProjectRole


class InvitationCreate(BaseSchema):
    role: ProjectRole = ProjectRole.MEMBER
    email: EmailStr | None = None


class InvitationRead(BaseSchema):
    token: str
    project_id: int
    role: ProjectRole
    email: str | None
    expires_at: datetime
    link: str


class InvitationAcceptResponse(BaseSchema):
    project_id: int
    message: str
