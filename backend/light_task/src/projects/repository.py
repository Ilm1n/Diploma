from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.projects.models import Project, ProjectMember


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_member(
        self,
        *,
        project_id: int,
        user_id: int,
        with_user: bool = False,
    ) -> ProjectMember | None:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        if with_user:
            stmt = stmt.options(selectinload(ProjectMember.user))
        return await self.session.scalar(stmt)

    def save_member(self, member: ProjectMember) -> None:
        self.session.add(member)

    async def delete_member(self, member: ProjectMember) -> None:
        await self.session.delete(member)

    async def touch_project(self, project_id: int) -> None:
        await self.session.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(updated_at=func.now())
        )

    async def flush(self) -> None:
        await self.session.flush()

    async def get_project_member_user_ids(self, project_id: int) -> list[int]:
        stmt = select(ProjectMember.user_id).where(
            ProjectMember.project_id == project_id
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_project_updated_at(self, project_id: int):
        stmt = select(Project.updated_at).where(Project.id == project_id)
        return await self.session.scalar(stmt)
