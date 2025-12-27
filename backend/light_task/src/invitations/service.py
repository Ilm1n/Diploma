import secrets
from datetime import datetime, timedelta, timezone
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.touch import touch_project
from src.invitations.models import ProjectInvitation
from src.invitations.schemas import (
    InvitationCreate,
    InvitationRead,
    InvitationAcceptResponse,
)
from src.projects.models import ProjectMember
from src.users.models import User

BASE_URL = "http://localhost:5173/invite"


class InvitationService:
    @staticmethod
    async def create_invitation(
        session: AsyncSession,
        project_id: int,
        inviter_id: int,
        data: InvitationCreate,
    ) -> InvitationRead:
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
        session.add(invite)
        await touch_project(session, project_id)
        await session.commit()

        return InvitationRead(**invite.__dict__, link=f"{BASE_URL}/{token}")

    @staticmethod
    async def get_project_invitations(
        session: AsyncSession,
        project_id: int,
    ) -> Sequence[ProjectInvitation]:
        query = (
            select(ProjectInvitation)
            .where(ProjectInvitation.project_id == project_id)
            .order_by(ProjectInvitation.created_at.desc())
        )
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete_invitation(
        session: AsyncSession,
        invitation_id: int,
        project_id: int,
    ) -> None:
        query = select(ProjectInvitation).where(
            ProjectInvitation.id == invitation_id,
            ProjectInvitation.project_id == project_id,
        )
        invite = await session.scalar(query)
        if invite:
            await session.delete(invite)
            await session.commit()

    @staticmethod
    async def accept_invitation(
        session: AsyncSession,
        token: str,
        user: User,
    ) -> InvitationAcceptResponse:
        query = (
            select(ProjectInvitation)
            .where(ProjectInvitation.token == token)
            .with_for_update()
        )
        invite = await session.scalar(query)

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
            ProjectMember.user_id == user.id,
        )
        existing_member = await session.scalar(member_check)

        if existing_member:
            return InvitationAcceptResponse(
                project_id=invite.project_id,
                message="You are already a member of this project",
            )

        new_member = ProjectMember(
            project_id=invite.project_id, user_id=user.id, role=invite.role
        )
        session.add(new_member)

        invite.used_count += 1

        session.add(invite)
        await touch_project(session, invite.project_id)

        await session.commit()

        return InvitationAcceptResponse(
            project_id=invite.project_id, message="Successfully joined the project"
        )
