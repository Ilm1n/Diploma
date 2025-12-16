import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.invitations.models import ProjectInvitation
from src.invitations.schemas import (
    InvitationCreate,
    InvitationRead,
    InvitationAcceptResponse,
)
from src.projects.models import ProjectMember
from src.users.models import User

INVITATION_TTL_DAYS = settings.invite.INVITATION_TTL_DAYS
BASE_URL = settings.invite.BASE_URL


class InvitationService:
    @staticmethod
    async def create_invitation(
        session: AsyncSession,
        project_id: int,
        inviter_id: int,
        data: InvitationCreate,
    ) -> InvitationRead:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=INVITATION_TTL_DAYS)

        invite = ProjectInvitation(
            token=token,
            project_id=project_id,
            inviter_id=inviter_id,
            role=data.role,
            email=data.email,
            expires_at=expires_at,
        )
        session.add(invite)
        await session.commit()

        return InvitationRead(
            token=invite.token,
            project_id=invite.project_id,
            role=invite.role,
            email=invite.email,
            expires_at=invite.expires_at,
            link=f"{BASE_URL}/{token}",
        )

    @staticmethod
    async def accept_invitation(
        session: AsyncSession,
        token: str,
        user: User,
    ) -> InvitationAcceptResponse:
        query = select(ProjectInvitation).where(ProjectInvitation.token == token)
        invite = await session.scalar(query)

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invitation token"
            )

        if invite.is_used:
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Invitation already used"
            )

        if invite.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Invitation expired"
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

        if invite.email:
            invite.is_used = True
            session.add(invite)

        await session.commit()

        return InvitationAcceptResponse(
            project_id=invite.project_id, message="Successfully joined the project"
        )
