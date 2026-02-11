from pydantic import EmailStr, Field

from src.schemas import BaseSchema


class UserBase(BaseSchema):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase):
    id: int
    is_active: bool
    full_name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = Field(None, max_length=512)


class UserUpdate(BaseSchema):
    username: str | None = Field(None, min_length=1, max_length=50)
    full_name: str | None = Field(None, min_length=1, max_length=255)


class UserPublic(BaseSchema):
    id: int
    username: str
    full_name: str | None
    avatar_url: str | None
    email: EmailStr
