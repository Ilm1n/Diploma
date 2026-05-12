from __future__ import annotations

from src.errors import ErrorCode
from src.projects.constants import ProjectRole
from src.projects.models import ProjectMember
from src.shared.errors import BadRequestError, ForbiddenError, NotFoundError


class ProjectMemberPolicy:
    def ensure_role_allowed(
        self,
        *,
        requester_member: ProjectMember | None,
        allowed_roles: list[ProjectRole],
    ) -> None:
        if requester_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if requester_member.role not in allowed_roles:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

    def ensure_project_member_can_read(
        self,
        *,
        requester_member: ProjectMember | None,
    ) -> None:
        if requester_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

    def ensure_project_owner(
        self,
        *,
        requester_member: ProjectMember | None,
    ) -> None:
        if requester_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if requester_member.role != ProjectRole.OWNER:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

    def ensure_can_remove_member(
        self,
        *,
        requester_member: ProjectMember | None,
        target_member: ProjectMember,
    ) -> None:
        if requester_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if requester_member.role == ProjectRole.MEMBER:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

        if target_member.role == ProjectRole.OWNER:
            raise ForbiddenError(ErrorCode.CANNOT_REMOVE_OWNER)

        if (
            requester_member.role == ProjectRole.MANAGER
            and target_member.role == ProjectRole.MANAGER
        ):
            raise ForbiddenError(ErrorCode.MANAGERS_CANNOT_REMOVE)

    def ensure_can_update_member_role(
        self,
        *,
        requester_member: ProjectMember | None,
        target_member: ProjectMember,
    ) -> None:
        if requester_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if requester_member.role != ProjectRole.OWNER:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

        if target_member.role == ProjectRole.OWNER:
            raise BadRequestError(ErrorCode.CANNOT_CHANGE_OWNER_ROLE)
