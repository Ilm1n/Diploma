from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.projects.constants import ProjectRole
from src.projects.models import Project, ProjectMember
from src.projects.schemas import ProjectCreate, ProjectUpdate, ProjectRead
from src.users.models import User


class ProjectService:
    @staticmethod
    async def create_project(
        session: AsyncSession,
        user: User,
        project_in: ProjectCreate,
    ) -> ProjectRead:
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

        return ProjectRead(**new_project.__dict__, current_user_role=ProjectRole.OWNER)

    @staticmethod
    async def get_user_projects(
        session: AsyncSession,
        user: User,
    ) -> Sequence[ProjectRead]:
        query = (
            select(Project, ProjectMember.role)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
        result = await session.execute(query)
        rows = result.all()

        return [
            ProjectRead(**proj.__dict__, current_user_role=role) for proj, role in rows
        ]

    @staticmethod
    async def get_project_details(
        session: AsyncSession,
        project_id: int,
        user: User,
    ) -> ProjectRead:
        query = (
            select(Project, ProjectMember.role)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(
                Project.id == project_id,
                ProjectMember.user_id == user.id,
            )
        )
        result = await session.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

        project, role = row
        return ProjectRead(**project.__dict__, current_user_role=role)

    @staticmethod
    async def update_project(
        session: AsyncSession,
        project: Project,
        project_update: ProjectUpdate,
    ) -> ProjectRead:
        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        session.add(project)
        await session.commit()
        await session.refresh(project)

        return ProjectRead(**project.__dict__)

    @staticmethod
    async def delete_project(
        session: AsyncSession,
        project: Project,
    ) -> None:
        await session.delete(project)
        await session.commit()
