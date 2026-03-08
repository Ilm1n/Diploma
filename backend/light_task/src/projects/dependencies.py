from typing import Annotated, List

from fastapi import Depends, HTTPException, status, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.errors import ErrorCode
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
                detail=ErrorCode.PROJECT_NOT_FOUND,
            )

        if member.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
            )

        return member.project


class ProjectPermissionChecker:
    def __init__(self, allowed_roles: List[ProjectRole]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        project_id: Annotated[int, Path()],
        user: Annotated[UserPayload, Depends(get_current_user)],
        session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    ) -> None:
        query = select(ProjectMember.role).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.sub,
        )

        member_role = await session.scalar(query)
        if member_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PROJECT_NOT_FOUND,
            )

        if member_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.INSUFFICIENT_PERMISSIONS,
            )


# Use `require_*` when route needs a loaded `Project` object; use `check_*` for role-only checks.
require_project_owner = ProjectAccessChecker([ProjectRole.OWNER])
require_project_manager = ProjectAccessChecker([ProjectRole.OWNER, ProjectRole.MANAGER])
require_project_member = ProjectAccessChecker(
    [ProjectRole.OWNER, ProjectRole.MANAGER, ProjectRole.MEMBER]
)

check_project_owner = ProjectPermissionChecker([ProjectRole.OWNER])
check_project_manager = ProjectPermissionChecker([ProjectRole.OWNER, ProjectRole.MANAGER])
check_project_member = ProjectPermissionChecker(
    [ProjectRole.OWNER, ProjectRole.MANAGER, ProjectRole.MEMBER]
)
