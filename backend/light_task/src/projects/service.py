from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.common.touch import touch_project
from src.db.database import db_helper
from src.logger import project_logger
from src.projects.constants import ProjectRole
from src.projects.models import Project, ProjectMember
from src.projects.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectRead,
    ProjectMemberUpdate,
)
from src.tags.constants import DEFAULT_PROJECT_TAGS
from src.tags.models import Tag


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_project(
        self,
        user_id: int,
        project_in: ProjectCreate,
    ) -> ProjectRead:
        new_project = Project(
            name=project_in.name,
            description=project_in.description,
            color=project_in.color,
            owner_id=user_id,
        )
        self.session.add(new_project)
        await self.session.flush()

        member = ProjectMember(
            project_id=new_project.id,
            user_id=user_id,
            role=ProjectRole.OWNER,
        )
        self.session.add(member)

        default_tags = [
            Tag(
                name=tag_data["name"],
                color=tag_data["color"],
                project_id=new_project.id,
            )
            for tag_data in DEFAULT_PROJECT_TAGS
        ]
        self.session.add_all(default_tags)

        try:
            await self.session.commit()
            await self.session.refresh(new_project)
            project_logger.info(f"Project created: {new_project.id} by user {user_id}")
        except Exception as e:
            await self.session.rollback()
            project_logger.exception(f"Failed to create project for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project",
            )

        return ProjectRead(
            id=new_project.id,
            name=new_project.name,
            description=new_project.description,
            color=new_project.color,
            owner_id=new_project.owner_id,
            created_at=new_project.created_at,
            updated_at=new_project.updated_at,
            current_user_role=ProjectRole.OWNER,
        )

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
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
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

    async def update_project(
        self,
        project: Project,
        project_update: ProjectUpdate,
    ) -> ProjectRead:
        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        project.updated_at = datetime.now(timezone.utc)

        self.session.add(project)
        try:
            await self.session.commit()
            await self.session.refresh(project)
            project_logger.info(f"Project updated: {project.id}")
        except Exception as e:
            await self.session.rollback()
            project_logger.exception(f"Failed to update project {project.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update project",
            )

        return ProjectRead(
            id=project.id,
            name=project.name,
            description=project.description,
            color=project.color,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            current_user_role=ProjectRole.OWNER,
        )

    async def delete_project(
        self,
        project: Project,
    ) -> None:
        await self.session.delete(project)
        try:
            await self.session.commit()
            project_logger.info(f"Project deleted: {project.id}")
        except Exception as e:
            await self.session.rollback()
            project_logger.exception(f"Failed to delete project {project.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete project",
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

    async def remove_member(
        self,
        project_id: int,
        user_id: int,
        requester_id: int,
    ) -> None:
        target_query = select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        target_member = await self.session.scalar(target_query)

        if not target_member:
            raise HTTPException(status_code=404, detail="Member not found")

        requester_query = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == requester_id,
        )
        requester_member = await self.session.scalar(requester_query)

        if not requester_member:
            raise HTTPException(
                status_code=403, detail="You are not a member of this project"
            )

        if target_member.role == ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove project owner",
            )

        if (
            requester_member.role == ProjectRole.MANAGER
            and target_member.role == ProjectRole.MANAGER
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot remove other managers. Ask the Owner.",
            )

        await self.session.delete(target_member)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            project_logger.info(f"Member {user_id} removed from project {project_id}")
        except Exception as e:
            await self.session.rollback()
            project_logger.exception(
                f"Failed to remove member {user_id} from project {project_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member",
            )

    async def update_member_role(
        self,
        project_id: int,
        user_id: int,
        data: ProjectMemberUpdate,
    ) -> ProjectMember:
        query = (
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .options(selectinload(ProjectMember.user))
        )
        member = await self.session.scalar(query)

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
            )

        if member.role == ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role of project owner",
            )

        member.role = data.role
        self.session.add(member)
        try:
            await self.session.commit()
            await touch_project(self.session, project_id)
            await self.session.refresh(member)
            project_logger.info(
                f"Member {user_id} role updated to {data.role} in project {project_id}"
            )
        except Exception as e:
            await self.session.rollback()
            project_logger.exception(
                f"Failed to update member {user_id} role in project {project_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member role",
            )
        return member


def get_project_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> ProjectService:
    return ProjectService(session)
