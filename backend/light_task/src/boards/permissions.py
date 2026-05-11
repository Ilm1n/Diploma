from __future__ import annotations

from src.errors import ErrorCode
from src.projects.constants import ProjectRole
from src.projects.models import ProjectMember
from src.shared.errors import ForbiddenError, NotFoundError


class BoardPermissions:
    def ensure_project_member_can_read(
        self,
        *,
        actor_member: ProjectMember | None,
    ) -> None:
        if actor_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

    def ensure_task_read_allowed(
        self,
        *,
        actor_member: ProjectMember | None,
    ) -> None:
        if actor_member is None:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

    def ensure_can_manage_columns(
        self,
        *,
        actor_member: ProjectMember | None,
    ) -> None:
        if actor_member is None:
            raise NotFoundError(ErrorCode.PROJECT_NOT_FOUND)

        if actor_member.role not in [ProjectRole.OWNER, ProjectRole.MANAGER]:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

    def ensure_task_assignee_allowed(
        self,
        *,
        actor_member: ProjectMember | None,
        actor_user_id: int,
        assignee_id: int | None,
    ) -> None:
        if (
            actor_member is not None
            and actor_member.role == ProjectRole.MEMBER
            and assignee_id is not None
            and assignee_id != actor_user_id
        ):
            raise ForbiddenError(ErrorCode.MEMBERS_ONLY_OWN_TASKS)

    def ensure_task_update_allowed(
        self,
        *,
        actor_member: ProjectMember | None,
        actor_user_id: int,
        task_assignee_id: int | None,
    ) -> None:
        if actor_member is None:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

        if actor_member.role in [ProjectRole.OWNER, ProjectRole.MANAGER]:
            return

        if task_assignee_id != actor_user_id:
            raise ForbiddenError(ErrorCode.MEMBERS_ONLY_OWN_TASKS)

    def ensure_task_delete_allowed(
        self,
        *,
        actor_member: ProjectMember | None,
    ) -> None:
        if actor_member is None:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)

        if actor_member.role not in [ProjectRole.OWNER, ProjectRole.MANAGER]:
            raise ForbiddenError(ErrorCode.INSUFFICIENT_PERMISSIONS)
