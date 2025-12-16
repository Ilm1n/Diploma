from datetime import datetime
from pydantic import Field, EmailStr
from src.core.schemas import BaseSchema
from src.projects.constants import ProjectRole


class InvitationCreate(BaseSchema):
    role: ProjectRole = ProjectRole.MEMBER
    email: EmailStr | None = None
    max_uses: int | None = Field(
        1, ge=1, description="Сколько раз можно использовать ссылку. None = безлимит."
    )
    expires_in_days: int = Field(7, ge=1, le=30, description="Срок действия в днях")


class InvitationRead(BaseSchema):
    id: int
    token: str
    role: ProjectRole
    email: str | None
    max_uses: int | None
    used_count: int
    expires_at: datetime
    link: str


class InvitationAcceptResponse(BaseSchema):
    project_id: int
    message: str
