from enum import StrEnum


class ProjectRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    MEMBER = "member"