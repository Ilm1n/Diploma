from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    BackgroundTasks,
)

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.s3 import S3Client, get_s3_client
from src.users.dependencies import valid_avatar
from src.users.schemas import (
    UserCreate,
    UserPasswordUpdate,
    UserRead,
    UserUpdate,
    UserPublic,
)
from src.users.service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_in: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return await user_service.create_user(user_in)


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    return await user_service.get_user_by_id(current_user.sub)


@router.patch("/me", response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_db = await user_service.get_user_by_id(current_user.sub)
    return await user_service.update_user(user=user_db, user_update=user_update)


@router.patch("/me/password", response_model=UserRead)
async def update_user_password(
    password_update: UserPasswordUpdate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    user_db = await user_service.get_user_by_id(current_user.sub)
    return await user_service.update_password(
        user=user_db,
        password_update=password_update,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[UserPayload, Depends(get_current_user)],
):
    return await user_service.get_user_by_id(user_id)


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file_data: Annotated[tuple[bytes, str, str], Depends(valid_avatar)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    bg_tasks: BackgroundTasks,
):
    content, ext, mime = file_data

    user_db = await user_service.get_user_by_id(current_user.sub)

    return await user_service.upload_avatar(
        user=user_db,
        file_data=content,
        extension=ext,
        mime_type=mime,
        s3_client=s3_client,
        background_tasks=bg_tasks,
    )


@router.delete("/me/avatar", response_model=UserRead)
async def delete_avatar(
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    bg_tasks: BackgroundTasks,
):
    user_db = await user_service.get_user_by_id(current_user.sub)

    return await user_service.delete_avatar(
        user=user_db,
        s3_client=s3_client,
        background_tasks=bg_tasks,
    )
