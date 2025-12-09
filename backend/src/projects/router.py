from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.db.database import db_helper
from src.users.models import User
from src.auth.dependencies import get_current_user
from src.projects.models import Project, ProjectMember
from src.projects.schemas import ProjectCreate, ProjectRead


router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
        project_in: ProjectCreate,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(db_helper.get_async_session)
):
    new_project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id
    )
    session.add(new_project)

    await session.flush()