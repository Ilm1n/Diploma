from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.db.database import db_helper
from src.users.models import User
from src.auth.dependencies import get_current_user
from src.projects.models import Project, ProjectMember
from src.projects.schemas import ProjectCreate, ProjectRead
from src.core.constants.role import ProjectRole


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    new_project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id,
    )
    session.add(new_project)

    await session.flush()

    member = ProjectMember(
        project_id=new_project.id, user_id=current_user.id, role=ProjectRole.OWNER
    )

    session.add(member)
    await session.commit()
    await session.refresh(new_project)

    return new_project


@router.get("/", response_model=list[ProjectRead])
async def get_my_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    query = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )

    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_details(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    query = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(Project.id == project_id)
        .where(ProjectMember.user_id == current_user.id)
    )

    result = await session.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project
