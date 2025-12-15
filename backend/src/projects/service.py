from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status, HTTPException

from src.projects.constants import ProjectRole
from src.projects.models import Project, ProjectMember
from src.projects.schemas import ProjectCreate, ProjectUpdate
from src.users.models import User


class ProjectService:
    @staticmethod
    async def create_project(
        session: AsyncSession,
        user: User,
        project_in: ProjectCreate,
    ) -> Project:
        new_project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=user.id,
        )
        session.add(new_project)
        await session.flush()

        member = ProjectMember(
            project_id=new_project.id,
            user_id=user.id,
            role=ProjectRole.OWNER,
        )
        session.add(member)

        await session.commit()
        await session.refresh(new_project)
        return new_project

    @staticmethod
    async def get_user_projects(
        session: AsyncSession,
        user: User,
    ) -> Sequence[Project]:
        query = (
            select(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_project_by_id(
        session: AsyncSession,
        project_id: int,
        user: User,
    ) -> Project | None:
        query = (
            select(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(
                Project.id == project_id,
                ProjectMember.user_id == user.id,
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_project(
        session: AsyncSession,
        project_id: int,
        project_update: ProjectUpdate,
        member: ProjectMember,
    ) -> Project:
        if member.role != ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can edit project settings",
            )

        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    @staticmethod
    async def delete_project(
        session: AsyncSession,
        project_id: int,
        member: ProjectMember,
    ) -> None:
        if member.role != ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can delete the project",
            )

        project = await session.get(Project, project_id)
        if project:
            await session.delete(project)
            await session.commit()
