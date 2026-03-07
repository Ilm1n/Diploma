from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.projects.dependencies import (
    check_project_manager,
    check_project_member,
    check_project_owner,
    require_project_owner,
)
from src.projects.models import Project
from src.projects.schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectMemberRead,
    ProjectMemberUpdate,
)
from src.projects.service import ProjectService, get_project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_in: ProjectCreate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    return await project_service.create_project(
        user_id=current_user.sub, project_in=project_in
    )


@router.get("/", response_model=list[ProjectRead])
async def get_my_projects(
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    return await project_service.get_user_projects(user_id=current_user.sub)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_details(
    project_id: int,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    return await project_service.get_project_details(
        project_id=project_id, user_id=current_user.sub
    )


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    project: Annotated[Project, Depends(require_project_owner)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    return await project_service.update_project(
        project=project,
        project_update=project_update,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    project: Annotated[Project, Depends(require_project_owner)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    await project_service.delete_project(project)


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def get_project_members(
    project_id: int,
    _: Annotated[None, Depends(check_project_member)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    return await project_service.get_project_members(project_id)


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_project_member(
    project_id: int,
    user_id: int,
    _: Annotated[None, Depends(check_project_manager)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    await project_service.remove_member(
        project_id=project_id, user_id=user_id, requester_id=current_user.sub
    )


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberRead)
async def update_member_role(
    project_id: int,
    user_id: int,
    member_update: ProjectMemberUpdate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    _: Annotated[None, Depends(check_project_owner)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
):
    return await project_service.update_member_role(
        project_id=project_id,
        user_id=user_id,
        data=member_update,
        requester_id=current_user.sub,
    )
