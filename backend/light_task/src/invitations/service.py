import secrets
from datetime import datetime, timedelta, timezone
from collections.abc import Sequence
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserPayload
from src.common.touch import touch_project
from src.config import settings
from src.db.database import db_helper
from src.errors import ErrorCode, SuccessCode
from src.logger import invitation_logger
from src.invitations.models import ProjectInvitation
from src.invitations.schemas import (
    InvitationCreate,
    InvitationAcceptResponse,
    SuccessPayload,
)
from src.projects.constants import ProjectRole
from src.projects.models import Project, ProjectMember
from src.realtimev1.dependencies import get_event_publisher
from src.realtimev1.domain_helpers import dump_invitation, get_project_member_user_ids
from src.realtimev1.events import RealtimeAudience, RealtimeEventType, RealtimeScope
from src.realtimev1.publisher import DomainEventPublisher

BASE_URL = settings.invite.base_url


class InvitationService:
    def __init__(self, session: AsyncSession, event_publisher: DomainEventPublisher):
        self.session = session
        self.event_publisher = event_publisher

    async def create_invitation(
        self,
        project_id: int,
        inviter_id: int,
        data: InvitationCreate,
        client_mutation_id: str | None = None,
    ) -> ProjectInvitation:
        inviter_member = await self.session.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == inviter_id,
            )
        )
        if not inviter_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.NOT_A_PROJECT_MEMBER,
            )

        if inviter_member.role == ProjectRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
            )

        if data.role == ProjectRole.OWNER and inviter_member.role != ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
            )

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)

        invite = ProjectInvitation(
            token=token,
            project_id=project_id,
            inviter_id=inviter_id,
            role=data.role,
            email=data.email,
            max_uses=data.max_uses,
            expires_at=expires_at,
        )
        self.session.add(invite)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            await self.session.refresh(invite)
            invitation_logger.info(f"Invitation created for project {project_id}")
        except Exception as e:
            await self.session.rollback()
            invitation_logger.exception(
                f"Failed to create invitation for project {project_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.INVITATION_CREATED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=inviter_id,
            project_id=project_id,
            payload={"invitation": dump_invitation(invite)},
            audience=RealtimeAudience.MANAGER,
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=inviter_id,
            reason=RealtimeEventType.INVITATION_CREATED,
            client_mutation_id=client_mutation_id,
        )

        return invite

    async def get_project_invitations(
        self,
        project_id: int,
    ) -> Sequence[ProjectInvitation]:
        query = (
            select(ProjectInvitation)
            .where(ProjectInvitation.project_id == project_id)
            .order_by(ProjectInvitation.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_invitation(
        self,
        invitation_id: int,
        project_id: int,
        actor_user_id: int,
        client_mutation_id: str | None = None,
    ) -> None:
        query = select(ProjectInvitation).where(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project_id,
        )
        invite = await self.session.scalar(query)
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.INVITATION_NOT_FOUND,
            )

        await self.session.delete(invite)
        await touch_project(self.session, project_id)
        try:
            await self.session.commit()
            invitation_logger.info(f"Invitation deleted: {invitation_id}")
        except Exception as e:
            await self.session.rollback()
            invitation_logger.exception(
                f"Failed to delete invitation {invitation_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.INVITATION_DELETED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=actor_user_id,
            project_id=project_id,
            payload={"invitationId": invitation_id},
            audience=RealtimeAudience.MANAGER,
            client_mutation_id=client_mutation_id,
        )
        await self._publish_project_list_item_updated(
            project_id=project_id,
            actor_user_id=actor_user_id,
            reason=RealtimeEventType.INVITATION_DELETED,
            client_mutation_id=client_mutation_id,
        )

    async def accept_invitation(
        self,
        token: str,
        user: UserPayload,
        client_mutation_id: str | None = None,
    ) -> InvitationAcceptResponse:
        query = (
            select(ProjectInvitation)
            .where(ProjectInvitation.token == token)
            .with_for_update()
        )
        invite = await self.session.scalar(query)

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.INVITATION_NOT_FOUND,
            )

        if invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail=ErrorCode.INVITATION_EXPIRED
            )

        if invite.max_uses is not None and invite.used_count >= invite.max_uses:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=ErrorCode.INVITATION_USAGE_LIMIT_REACHED,
            )

        if invite.email and invite.email != user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INVITATION_FOR_OTHER_EMAIL,
            )

        member_check = select(ProjectMember).where(
            ProjectMember.project_id == invite.project_id,
            ProjectMember.user_id == user.sub,
        )
        existing_member = await self.session.scalar(member_check)

        if existing_member:
            return InvitationAcceptResponse(
                project_id=invite.project_id,
                success=SuccessPayload(code=SuccessCode.ALREADY_PROJECT_MEMBER),
            )

        new_member = ProjectMember(
            project_id=invite.project_id, user_id=user.sub, role=invite.role
        )
        self.session.add(new_member)

        invite.used_count += 1

        self.session.add(invite)
        await touch_project(self.session, invite.project_id)

        try:
            await self.session.commit()
            await self.session.refresh(new_member)
            invitation_logger.info(
                f"Invitation accepted by user {user.sub} for project {invite.project_id}"
            )
        except Exception as e:
            await self.session.rollback()
            invitation_logger.exception(
                f"Failed to accept invitation for user {user.sub}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )

        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.MEMBER_ADDED,
            scope=RealtimeScope.PROJECT,
            actor_user_id=user.sub,
            project_id=invite.project_id,
            payload={
                "userId": user.sub,
                "role": new_member.role,
            },
            client_mutation_id=client_mutation_id,
        )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_ADDED_TO_USER,
            scope=RealtimeScope.USER,
            actor_user_id=user.sub,
            user_ids=[user.sub],
            project_id=invite.project_id,
            payload={"projectId": invite.project_id},
            client_mutation_id=client_mutation_id,
        )
        affected_user_ids = await get_project_member_user_ids(self.session, invite.project_id)
        await self._publish_project_list_item_updated(
            project_id=invite.project_id,
            actor_user_id=user.sub,
            user_ids=affected_user_ids,
            reason=RealtimeEventType.MEMBER_ADDED,
            client_mutation_id=client_mutation_id,
        )

        return InvitationAcceptResponse(
            project_id=invite.project_id,
            success=SuccessPayload(code=SuccessCode.INVITATION_ACCEPT_SUCCESS),
        )

    async def _publish_project_list_item_updated(
        self,
        *,
        project_id: int,
        actor_user_id: int,
        reason: str | RealtimeEventType,
        client_mutation_id: str | None,
        user_ids: list[int] | None = None,
    ) -> None:
        affected_user_ids = user_ids or await get_project_member_user_ids(
            self.session,
            project_id,
        )
        if not affected_user_ids:
            return

        project_updated_at = await self.session.scalar(
            select(Project.updated_at).where(Project.id == project_id)
        )
        await self.event_publisher.publish_event(
            event_type=RealtimeEventType.PROJECT_LIST_ITEM_UPDATED,
            scope=RealtimeScope.USER,
            actor_user_id=actor_user_id,
            user_ids=affected_user_ids,
            project_id=project_id,
            payload={
                "projectId": project_id,
                "updatedAt": project_updated_at,
                "reason": str(reason),
            },
            client_mutation_id=client_mutation_id,
        )


def get_invitation_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> InvitationService:
    return InvitationService(session, event_publisher)
