from __future__ import annotations

from dataclasses import dataclass

from src.projects.constants import ProjectRole


@dataclass(frozen=True, kw_only=True)
class CreateInvitationCommand:
    project_id: int
    inviter_id: int
    role: ProjectRole
    email: str | None
    max_uses: int | None
    expires_in_days: int
    client_mutation_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class ListProjectInvitationsQuery:
    project_id: int
    actor_user_id: int


@dataclass(frozen=True, kw_only=True)
class DeleteInvitationCommand:
    invitation_id: int
    project_id: int
    actor_user_id: int
    client_mutation_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class AcceptInvitationCommand:
    token: str
    user_id: int
    user_email: str
    client_mutation_id: str | None = None
