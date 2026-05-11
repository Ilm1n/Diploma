from __future__ import annotations

from collections.abc import Callable

from src.db.unit_of_work import UnitOfWork
from src.errors import ErrorCode
from src.logger import project_logger
from src.projects.dto import RemoveMemberCommand, UpdateMemberRoleCommand
from src.projects.events import MemberRemoved, MemberRoleChanged
from src.projects.models import ProjectMember
from src.projects.permissions import ProjectMemberPolicy
from src.projects.repository import ProjectRepository
from src.shared.errors import AppError, DatabaseError, NotFoundError


class RemoveMemberUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        policy: ProjectMemberPolicy | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._policy = policy or ProjectMemberPolicy()

    async def execute(self, command: RemoveMemberCommand) -> None:
        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("UnitOfWork has not been entered")

                repository = ProjectRepository(uow.session)
                target_member = await repository.get_member(
                    project_id=command.project_id,
                    user_id=command.user_id,
                )
                if target_member is None:
                    raise NotFoundError(ErrorCode.MEMBER_NOT_FOUND)

                requester_member = await repository.get_member(
                    project_id=command.project_id,
                    user_id=command.requester_id,
                )
                self._policy.ensure_can_remove_member(
                    requester_member=requester_member,
                    target_member=target_member,
                )

                await repository.delete_member(target_member)
                await repository.touch_project(command.project_id)
                await repository.flush()
                remaining_user_ids = await repository.get_project_member_user_ids(
                    command.project_id
                )
                uow.collect_event(
                    MemberRemoved(
                        user_id=command.user_id,
                        remaining_user_ids=remaining_user_ids,
                        actor_user_id=command.requester_id,
                        project_id=command.project_id,
                        client_mutation_id=command.client_mutation_id,
                    )
                )
        except AppError:
            raise
        except Exception as exc:
            project_logger.exception(
                "Failed to remove member %s from project %s",
                command.user_id,
                command.project_id,
                exc_info=exc,
            )
            raise DatabaseError() from exc


class UpdateMemberRoleUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        policy: ProjectMemberPolicy | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._policy = policy or ProjectMemberPolicy()

    async def execute(self, command: UpdateMemberRoleCommand) -> ProjectMember:
        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("UnitOfWork has not been entered")

                repository = ProjectRepository(uow.session)
                target_member = await repository.get_member(
                    project_id=command.project_id,
                    user_id=command.user_id,
                    with_user=True,
                )
                if target_member is None:
                    raise NotFoundError(ErrorCode.MEMBER_NOT_FOUND)

                requester_member = await repository.get_member(
                    project_id=command.project_id,
                    user_id=command.requester_id,
                )
                self._policy.ensure_can_update_member_role(
                    requester_member=requester_member,
                    target_member=target_member,
                )

                previous_role = target_member.role
                target_member.role = command.role
                repository.save_member(target_member)
                await repository.touch_project(command.project_id)
                await repository.flush()
                affected_user_ids = await repository.get_project_member_user_ids(
                    command.project_id
                )
                uow.collect_event(
                    MemberRoleChanged(
                        user_id=command.user_id,
                        role=target_member.role,
                        previous_role=previous_role,
                        affected_user_ids=affected_user_ids,
                        actor_user_id=command.requester_id,
                        project_id=command.project_id,
                        client_mutation_id=command.client_mutation_id,
                    )
                )
                return target_member
        except AppError:
            raise
        except Exception as exc:
            project_logger.exception(
                "Failed to update member %s role in project %s",
                command.user_id,
                command.project_id,
                exc_info=exc,
            )
            raise DatabaseError() from exc
