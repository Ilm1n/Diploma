from __future__ import annotations

from dataclasses import dataclass

from src.projects.constants import ProjectRole


@dataclass(frozen=True, kw_only=True)
class CreateProjectCommand:
    owner_id: int
    name: str
    description: str | None
    color: str
    client_mutation_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class UpdateProjectCommand:
    project_id: int
    actor_user_id: int
    changes: dict[str, object]
    client_mutation_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class DeleteProjectCommand:
    project_id: int
    actor_user_id: int
    client_mutation_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class RemoveMemberCommand:
    project_id: int
    user_id: int
    requester_id: int
    client_mutation_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class UpdateMemberRoleCommand:
    project_id: int
    user_id: int
    role: ProjectRole
    requester_id: int
    client_mutation_id: str | None = None
