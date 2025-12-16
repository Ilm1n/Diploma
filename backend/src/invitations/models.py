from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db.base import Base
from src.projects.constants import ProjectRole

if TYPE_CHECKING:
    from src.projects.models import Project
    from src.users.models import User


class ProjectInvitation(Base):
    __tablename__ = "project_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    inviter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    role: Mapped[ProjectRole] = mapped_column(String(20), default=ProjectRole.MEMBER)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_used: Mapped[bool] = mapped_column(default=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped["Project"] = relationship("Project")
    inviter: Mapped["User"] = relationship("User")
