from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.invitations.schemas import (
    InvitationCreate,
    InvitationRead,
    InvitationAcceptResponse,
)
from src.invitations.service import InvitationService, get_invitation_service
from src.projects.dependencies import check_project_manager

router = APIRouter(tags=["Invitations"])


@router.post(
    "/projects/{project_id}/invite",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    project_id: int,
    invite_in: InvitationCreate,
    _: Annotated[None, Depends(check_project_manager)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
):
    return await invitation_service.create_invitation(
        project_id=project_id,
        inviter_id=current_user.sub,
        data=invite_in
    )


@router.get("/projects/{project_id}/invitations", response_model=list[InvitationRead])
async def get_project_invitations(
    project_id: int,
    _: Annotated[None, Depends(check_project_manager)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
):
    return await invitation_service.get_project_invitations(project_id)


@router.delete(
    "/projects/{project_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_invitation(
    project_id: int,
    invitation_id: int,
    _: Annotated[None, Depends(check_project_manager)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
):
    await invitation_service.delete_invitation(invitation_id, project_id)


@router.post(
    "/invitations/{token}/accept",
    response_model=InvitationAcceptResponse,
)
async def accept_invitation(
    token: str,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
):
    return await invitation_service.accept_invitation(token, current_user)
