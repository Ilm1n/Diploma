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
from src.invitations.models import ProjectInvitation
from src.invitations.schemas import (
    InvitationCreate,
    InvitationAcceptResponse,
)
from src.projects.models import ProjectMember

BASE_URL = settings.invite.base_url


class InvitationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_invitation(
        self,
        project_id: int,
        inviter_id: int,
        data: InvitationCreate,
    ) -> ProjectInvitation:
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
        await self.session.commit()

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
    ) -> None:
        query = select(ProjectInvitation).where(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project_id,
        )
        invite = await self.session.scalar(query)
        if invite:
            await self.session.delete(invite)
            await self.session.commit()

    async def accept_invitation(
        self,
        token: str,
        user: UserPayload,
    ) -> InvitationAcceptResponse:
        query = (
            select(ProjectInvitation)
            .where(ProjectInvitation.token == token)
            .with_for_update()
        )
        invite = await self.session.scalar(query)

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token"
            )

        if invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Invitation expired"
            )

        if invite.max_uses is not None and invite.used_count >= invite.max_uses:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation usage limit reached",
            )

        if invite.email and invite.email != user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation was sent to another email address",
            )

        member_check = select(ProjectMember).where(
            ProjectMember.project_id == invite.project_id,
            ProjectMember.user_id == user.sub,
        )
        existing_member = await self.session.scalar(member_check)

        if existing_member:
            return InvitationAcceptResponse(
                project_id=invite.project_id,
                message="You are already a member of this project",
            )

        new_member = ProjectMember(
            project_id=invite.project_id,
            user_id=user.sub,
            role=invite.role
        )
        self.session.add(new_member)

        invite.used_count += 1

        self.session.add(invite)
        await touch_project(self.session, invite.project_id)

        await self.session.commit()

        return InvitationAcceptResponse(
            project_id=invite.project_id, message="Successfully joined the project"
        )


def get_invitation_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> InvitationService:
    return InvitationService(session)