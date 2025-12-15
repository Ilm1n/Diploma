from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.db.database import db_helper
from src.projects.dependencies import get_project_member
from src.projects.models import ProjectMember
from src.projects.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from src.projects.service import ProjectService
from src.users.models import User

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_in: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await ProjectService.create_project(session, current_user, project_in)


@router.get("/", response_model=list[ProjectRead])
async def get_my_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await ProjectService.get_user_projects(session, current_user)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_details(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    project = await ProjectService.get_project_by_id(session, project_id, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    member: Annotated[ProjectMember, Depends(get_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await ProjectService.update_project(
        session=session,
        project_id=project_id,
        project_update=project_update,
        member=member,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    member: Annotated[ProjectMember, Depends(get_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await ProjectService.delete_project(session, project_id, member)
