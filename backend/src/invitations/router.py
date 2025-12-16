from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.db.database import db_helper
from src.invitations.schemas import (
    InvitationCreate,
    InvitationRead,
    InvitationAcceptResponse,
)
from src.invitations.service import InvitationService
from src.projects.dependencies import require_project_manager
from src.projects.models import Project
from src.users.models import User

router = APIRouter(tags=["Invitations"])


@router.post(
    "/projects/{project_id}/invite",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    project_id: int,
    invite_in: InvitationCreate,
    _: Annotated[Project, Depends(require_project_manager)],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await InvitationService.create_invitation(
        session, project_id, current_user.id, invite_in
    )


@router.get("/projects/{project_id}/invitations", response_model=list[InvitationRead])
async def get_project_invitations(
    project_id: int,
    _: Annotated[Project, Depends(require_project_manager)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await InvitationService.get_project_invitations(session, project_id)


@router.delete(
    "/projects/{project_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_invitation(
    project_id: int,
    invitation_id: int,
    _: Annotated[Project, Depends(require_project_manager)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await InvitationService.delete_invitation(session, invitation_id, project_id)


@router.post(
    "/invitations/{token}/accept",
    response_model=InvitationAcceptResponse,
)
async def accept_invitation(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await InvitationService.accept_invitation(session, token, current_user)
