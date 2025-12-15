from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.projects.models import Project, ProjectMember
from src.projects.schemas import ProjectCreate
from src.projects.constants import ProjectRole
from src.users.models import User


class ProjectService:
    @staticmethod
    async def create_project(
        session: AsyncSession, user: User, project_in: ProjectCreate
    ) -> Project:
        new_project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=user.id,
        )
        session.add(new_project)
        await session.flush()

        member = ProjectMember(
            project_id=new_project.id, user_id=user.id, role=ProjectRole.OWNER
        )
        session.add(member)

        await session.commit()
        await session.refresh(new_project)
        return new_project

    @staticmethod
    async def get_user_projects(session: AsyncSession, user: User) -> list[Project]:
        query = (
            select(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_project_by_id(
        session: AsyncSession, project_id: int, user: User
    ) -> Project | None:
        query = (
            select(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(Project.id == project_id)
            .where(ProjectMember.user_id == user.id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
