from collections.abc import Sequence
from datetime import datetime, timezone


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload


from src.common.touch import touch_project
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
           color=project_in.color,
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


       default_tags = [
           Tag(
               name=tag_data["name"],
               color=tag_data["color"],
               project_id=new_project.id,
           )
           for tag_data in DEFAULT_PROJECT_TAGS
       ]
       session.add_all(default_tags)


       await session.commit()
       await session.refresh(new_project)


       return ProjectRead(**new_project.__dict__,
                          current_user_role=ProjectRole.OWNER)


   @staticmethod
   async def get_user_projects(
           session: AsyncSession,
           user: User,
   ) -> Sequence[ProjectRead]:
       query = (
           select(Project, ProjectMember.role)
           .join(ProjectMember, Project.id == ProjectMember.project_id)
           .where(ProjectMember.user_id == user.id)
           .order_by(Project.updated_at.desc())
       )
       result = await session.execute(query)
       rows = result.all()


       return [
           ProjectRead(**proj.__dict__, current_user_role=role) for proj, role
           in rows
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
               status_code=status.HTTP_404_NOT_FOUND,
               detail="Project not found"
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


       project.updated_at = datetime.now(timezone.utc)


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


   @staticmethod
   async def get_project_members(
           session: AsyncSession,
           project_id: int,
   ) -> Sequence[ProjectMember]:
       query = (
           select(ProjectMember)
           .where(ProjectMember.project_id == project_id)
           .options(selectinload(ProjectMember.user))
           .order_by(ProjectMember.joined_at)
       )
       result = await session.execute(query)
       return result.scalars().all()


   @staticmethod
   async def remove_member(
           session: AsyncSession,
           project_id: int,
           user_id: int,
           requester_id: int,
   ) -> None:
       target_query = select(ProjectMember).where(
           ProjectMember.project_id == project_id,
           ProjectMember.user_id == user_id
       )
       target_member = await session.scalar(target_query)


       if not target_member:
           raise HTTPException(status_code=404, detail="Member not found")


       requester_query = select(ProjectMember).where(
           ProjectMember.project_id == project_id,
           ProjectMember.user_id == requester_id,
       )
       requester_member = await session.scalar(requester_query)


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


       await session.delete(target_member)
       await touch_project(session, project_id)
       await session.commit()


   @staticmethod
   async def update_member_role(
           session: AsyncSession,
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
       member = await session.scalar(query)


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
       session.add(member)
       await session.commit()
       await touch_project(session, project_id)
       await session.refresh(member)
       return member
