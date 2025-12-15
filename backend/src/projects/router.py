from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.db.database import db_helper
from src.projects.constants import ProjectRole
from src.projects.dependencies import (
    require_project_owner,
    require_project_manager,
    require_project_member,
)
from src.projects.models import Project
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


@router.get("/", response_model=List[ProjectRead])
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
    return await ProjectService.get_project_details(session, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    project: Annotated[Project, Depends(require_project_owner)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    updated_project = await ProjectService.update_project(
        session=session,
        project=project,
        project_update=project_update,
    )
    updated_project.current_user_role = ProjectRole.OWNER
    return updated_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    project: Annotated[Project, Depends(require_project_owner)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await ProjectService.delete_project(session, project)
