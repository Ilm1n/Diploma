from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.db.database import db_helper
from src.users.models import User
from src.users.schemas import UserCreate, UserRead, UserUpdate, UserPublic
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await UserService.create_user(session, user_in)


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await UserService.update_user(
        session=session, user=current_user, user_update=user_update
    )


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    _: Annotated[User, Depends(get_current_user)],
):
    return await UserService.get_user_by_id(session, user_id)


@router.post("/users/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: Annotated[UploadFile, File(description="Файл изображения (jpg, png, webp)")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )
    return await UserService.upload_avatar(session=session, user=user, file=file)
