from typing import Annotated

from fastapi import Path, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.database import db_helper
from src.projects.constants import ProjectRole
from src.projects.models import ProjectMember
from src.tags.models import Tag
from src.users.models import User


class TagAccessChecker:

    def __init__(self, required_roles: list[ProjectRole]):
        self.required_roles = required_roles

    async def __call__(
        self,
        tag_id: Annotated[int, Path(...)],
        user: Annotated[User, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    ) -> Tag:
        tag = await session.get(Tag, tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        query = select(ProjectMember).where(
            ProjectMember.project_id == tag.project_id, ProjectMember.user_id == user.id
        )
        member = (await session.execute(query)).scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of the project this tag belongs to",
            )

        if member.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage tags",
            )

        return tag


get_tag_for_write = TagAccessChecker([ProjectRole.OWNER, ProjectRole.MANAGER])
