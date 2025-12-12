from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Text, DateTime, func, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.projects.constants import ProjectRole
from src.core.db.base import Base
from src.core.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.boards.models import BoardColumn


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    board_columns: Mapped[list["BoardColumn"]] = relationship(
        "BoardColumn",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="members")

    __table_args__ = (UniqueConstraint("project_id", "user_id"),)
