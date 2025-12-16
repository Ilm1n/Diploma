from pydantic import Field, ConfigDict
from src.core.schemas import BaseSchema


class TagBase(BaseSchema):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", examples=["#FF0000"]
    )


class TagCreate(TagBase):
    pass


class TagUpdate(BaseSchema):
    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")


class TagRead(TagBase):
    id: int
    project_id: int
