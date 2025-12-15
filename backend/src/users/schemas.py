from pydantic import EmailStr, Field

from src.core.schemas import BaseSchema


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
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = Field(None, max_length=512)
