from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.db.database import db_helper
from src.s3 import S3Client, get_s3_client
from src.users.dependencies import valid_avatar
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


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file_data: Annotated[tuple[bytes, str, str], Depends(valid_avatar)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    bg_tasks: BackgroundTasks,
):
    content, ext, mime = file_data

    return await UserService.upload_avatar(
        session=session,
        user=user,
        file_data=content,
        extension=ext,
        mime_type=mime,
        s3_client=s3_client,
        background_tasks=bg_tasks,
    )

@router.delete("/me/avatar", response_model=UserRead)
async def delete_avatar(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    bg_tasks: BackgroundTasks,
):
    return await UserService.delete_avatar(
        session=session,
        user=user,
        s3_client=s3_client,
        background_tasks=bg_tasks,
    )
