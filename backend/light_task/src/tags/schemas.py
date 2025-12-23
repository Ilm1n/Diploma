from pydantic import Field

from src.constants import HEX_COLOR_PATTERN
from src.schemas import BaseSchema


class TagBase(BaseSchema):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#9CA3AF", pattern=HEX_COLOR_PATTERN)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseSchema):
    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, pattern=HEX_COLOR_PATTERN)


class TagRead(TagBase):
    id: int
    project_id: int
