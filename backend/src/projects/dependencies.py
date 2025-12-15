from typing import Annotated

from fastapi import Path, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.dependencies import get_current_user
from src.core.db.database import db_helper
from src.projects.models import ProjectMember
from src.users.models import User


async def get_project_member(
    project_id: Annotated[int, Path(..., description="Project ID")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> ProjectMember:
    query = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
    )
    member = (await session.execute(query)).scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this project",
        )
    return member
