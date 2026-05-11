from __future__ import annotations

from src.errors import ErrorCode
from src.projects.constants import ProjectRole
from src.projects.models import ProjectMember
from src.shared.errors import ForbiddenError, NotFoundError


class TagPermissions:
    def ensure_can_create_tag(self, member: ProjectMember | None) -> None:
        if member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if member.role not in [ProjectRole.OWNER, ProjectRole.MANAGER]:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

    def ensure_can_write_tag(self, member: ProjectMember | None) -> None:
        if member is None:
            raise ForbiddenError(ErrorCode.NOT_A_PROJECT_MEMBER)

        if member.role not in [ProjectRole.OWNER, ProjectRole.MANAGER]:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)
