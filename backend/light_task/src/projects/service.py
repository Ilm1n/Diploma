from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import db_helper
from src.errors import ErrorCode
from src.projects.models import Project, ProjectMember
from src.projects.schemas import ProjectRead


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_projects(
        self,
        user_id: int,
    ) -> Sequence[ProjectRead]:
        query = (
            select(Project, ProjectMember.role)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
            .order_by(Project.updated_at.desc())
        )
        result = await self.session.execute(query)
        rows = result.all()

        return [
            ProjectRead(
                id=proj.id,
                name=proj.name,
                description=proj.description,
                color=proj.color,
                owner_id=proj.owner_id,
                created_at=proj.created_at,
                updated_at=proj.updated_at,
                current_user_role=role,
            )
            for proj, role in rows
        ]

    async def get_project_details(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectRead:
        query = (
            select(Project, ProjectMember.role)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(
                Project.id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        result = await self.session.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PROJECT_NOT_FOUND,
            )

        project, role = row
        return ProjectRead(
            id=project.id,
            name=project.name,
            description=project.description,
            color=project.color,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            current_user_role=role,
        )

    async def get_project_members(
        self,
        project_id: int,
    ) -> Sequence[ProjectMember]:
        query = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .options(selectinload(ProjectMember.user))
            .order_by(ProjectMember.joined_at)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


def get_project_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> ProjectService:
    return ProjectService(session)
