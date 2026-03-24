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
from src.errors import ErrorCode
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
from src.realtimev1.dependencies import get_event_publisher
from src.realtimev1.domain_helpers import (
    dump_project,
    get_project_member_user_ids,
)
from src.realtimev1.events import RealtimeEventType, RealtimeScope
from src.realtimev1.publisher import DomainEventPublisher


class ProjectService:
    def __init__(self, session: AsyncSession, event_publisher: DomainEventPublisher):
        self.session = session
        self.event_publisher = event_publisher

    async def create_project(
        self,
        user_id: int,
        project_in: ProjectCreate,
        client_mutation_id: str | None = None,
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
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self._publish_project_added_to_user(
            project=new_project,
            user_id=user_id,
            actor_user_id=user_id,
            client_mutation_id=client_mutation_id,
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

    async def update_project(
        self,
        project: Project,
        project_update: ProjectUpdate,
        actor_user_id: int,
        client_mutation_id: str | None = None,
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
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self._publish_project_updated(
            project=project,
            actor_user_id=actor_user_id,
            client_mutation_id=client_mutation_id,
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
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> None:
        project_id = project.id
        affected_user_ids = await get_project_member_user_ids(self.session, project_id)

        await self.session.delete(project)
        try:
            await self.session.commit()
            project_logger.info(f"Project deleted: {project.id}")
        except Exception as e:
            await self.session.rollback()
            project_logger.exception(f"Failed to delete project {project.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_DELETED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"projectId": project_id},
            client_mutation_id=client_mutation_id,
        )
        if affected_user_ids:
            await self.event_publisher.publish_event(
                event_type=RealtimeEventType.PROJECT_REMOVED_FROM_USER,
                scope=RealtimeScope.USER,
                actor_user_id=actor_user_id,
                user_ids=affected_user_ids,
                project_id=project_id,
                payload={"projectId": project_id},
                client_mutation_id=client_mutation_id,
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
        client_mutation_id: str | None = None,
    ) -> None:
        target_query = select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        target_member = await self.session.scalar(target_query)

        if not target_member:
            raise HTTPException(status_code=404, detail=ErrorCode.MEMBER_NOT_FOUND)

        requester_query = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == requester_id,
        )
        requester_member = await self.session.scalar(requester_query)

        if not requester_member:
            raise HTTPException(
                status_code=403, detail=ErrorCode.NOT_A_PROJECT_MEMBER
            )

        if target_member.role == ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.CANNOT_REMOVE_OWNER,
            )

        if requester_member.role == ProjectRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
            )

        if (
            requester_member.role == ProjectRole.MANAGER
            and target_member.role == ProjectRole.MANAGER
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.MANAGERS_CANNOT_REMOVE,
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
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.MEMBER_REMOVED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=requester_id,
            project_id=project_id,
            payload={"userId": user_id},
            client_mutation_id=client_mutation_id,
        )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_REMOVED_FROM_USER,
            scope=RealtimeScope.USER,
            actor_user_id=requester_id,
            project_id=project_id,
            user_ids=[user_id],
            payload={"projectId": project_id},
            client_mutation_id=client_mutation_id,
        )

        remaining_user_ids = await get_project_member_user_ids(self.session, project_id)
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=requester_id,
            user_ids=remaining_user_ids,
            reason=RealtimeEventType.MEMBER_REMOVED,
            client_mutation_id=client_mutation_id,
        )

    async def update_member_role(
        self,
        project_id: int,
        user_id: int,
        data: ProjectMemberUpdate,
        requester_id: int,
        client_mutation_id: str | None = None,
    ) -> ProjectMember:
        requester_query = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == requester_id,
        )
        requester_member = await self.session.scalar(requester_query)

        if not requester_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.NOT_A_PROJECT_MEMBER,
            )

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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.MEMBER_NOT_FOUND,
            )

        if requester_member.role == ProjectRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
            )

        if requester_member.role == ProjectRole.MANAGER:
            if member.role in [ProjectRole.MANAGER, ProjectRole.OWNER]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
                )

        if member.role == ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.CANNOT_CHANGE_OWNER_ROLE,
            )

        previous_role = member.role
        member.role = data.role
        self.session.add(member)
        try:
            await touch_project(self.session, project_id)
            await self.session.commit()
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
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.MEMBER_ROLE_CHANGED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=requester_id,
            project_id=project_id,
            payload={
                "userId": user_id,
                "role": member.role,
                "previousRole": previous_role,
            },
            client_mutation_id=client_mutation_id,
        )

        affected_user_ids = await get_project_member_user_ids(self.session, project_id)
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=requester_id,
            user_ids=affected_user_ids,
            reason=RealtimeEventType.MEMBER_ROLE_CHANGED,
            client_mutation_id=client_mutation_id,
        )
        return member

    async def _publish_project_updated(
        self,
        *,
        project: Project,
        actor_user_id: int,
        client_mutation_id: str | None,
    ) -> None:
        payload = {"project": dump_project(project)}
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_UPDATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project.id,
            payload=payload,
            client_mutation_id=client_mutation_id,
        )
        affected_user_ids = await get_project_member_user_ids(self.session, project.id)
        await self._publish_project_list_item_updated(
            project_id=project.id,
            actor_user_id=actor_user_id,
            user_ids=affected_user_ids,
            reason=RealtimeEventType.PROJECT_UPDATED,
            client_mutation_id=client_mutation_id,
        )

    async def _publish_project_added_to_user(
        self,
        *,
        project: Project,
        user_id: int,
        actor_user_id: int,
        client_mutation_id: str | None,
    ) -> None:
        payload = {"project": dump_project(project, current_user_role=ProjectRole.OWNER)}
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_ADDED_TO_USER,
            scope=RealtimeScope.USER,
            actor_user_id=actor_user_id,
            project_id=project.id,
            user_ids=[user_id],
            payload=payload,
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project.id,
            actor_user_id=actor_user_id,
            user_ids=[user_id],
            reason=RealtimeEventType.PROJECT_ADDED_TO_USER,
            client_mutation_id=client_mutation_id,
        )

    async def _publish_project_list_item_updated(
        self,
        *,
        project_id: int,
        actor_user_id: int,
        user_ids: list[int],
        reason: str | RealtimeEventType,
        client_mutation_id: str | None,
    ) -> None:
        if not user_ids:
            return
        project_updated_at = await self.session.scalar(
            select(Project.updated_at).where(Project.id == project_id)
        )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_LIST_ITEM_UPDATED,
            scope=RealtimeScope.USER,
            actor_user_id=actor_user_id,
            user_ids=user_ids,
            project_id=project_id,
            payload={
                "projectId": project_id,
                "updatedAt": project_updated_at,
                "reason": str(reason),
            },
            client_mutation_id=client_mutation_id,
        )


def get_project_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> ProjectService:
    return ProjectService(session, event_publisher)
