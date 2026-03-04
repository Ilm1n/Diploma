from typing import Annotated, List

from fastapi import Depends, HTTPException, status, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.messages import MESSAGES
from src.db.database import db_helper
from src.projects.constants import ProjectRole
from src.projects.models import Project, ProjectMember


class ProjectAccessChecker:
    def __init__(self, allowed_roles: List[ProjectRole]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        project_id: Annotated[int, Path()],
        user: Annotated[UserPayload, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    ) -> Project:
        query = (
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.sub,
            )
            .options(selectinload(ProjectMember.project))
        )

        result = await session.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MESSAGES["PROJECT_NOT_FOUND"],
            )

        if member.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MESSAGES["INSUFFICIENT_PERMISSIONS"],
            )

        return member.project


require_project_owner = ProjectAccessChecker([ProjectRole.OWNER])
require_project_manager = ProjectAccessChecker([ProjectRole.OWNER, ProjectRole.MANAGER])
require_project_member = ProjectAccessChecker(
    [ProjectRole.OWNER, ProjectRole.MANAGER, ProjectRole.MEMBER]
)
