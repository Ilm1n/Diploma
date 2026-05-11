from __future__ import annotations

from src.errors import ErrorCode
from src.projects.constants import ProjectRole
from src.projects.models import ProjectMember
from src.shared.errors import ForbiddenError, NotFoundError


class InvitationPermissions:
    def ensure_can_manage_invitations(
        self,
        *,
        member: ProjectMember | None,
    ) -> None:
        if member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if member.role == ProjectRole.MEMBER:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

    def ensure_can_create_role(
        self,
        *,
        member: ProjectMember,
        role: ProjectRole,
    ) -> None:
        if role == ProjectRole.OWNER and member.role != ProjectRole.OWNER:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)
