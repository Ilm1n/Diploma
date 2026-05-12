from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
    BackgroundTasks,
)

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.db.database import db_helper
from src.db.unit_of_work import UnitOfWork
from src.s3 import S3Client, get_s3_client
from src.users.dependencies import valid_avatar
from src.users.dto import (
    GetUserQuery,
    RegisterUserCommand,
    UpdateUserCommand,
    UpdateUserPasswordCommand,
)
from src.users.schemas import (
    UserCreate,
    UserPasswordUpdate,
    UserRead,
    UserUpdate,
    UserPublic,
)
from src.users.service import UserService, get_user_service
from src.users.use_cases import (
    GetUserUseCase,
    RegisterUserUseCase,
    UpdateUserPasswordUseCase,
    UpdateUserUseCase,
)

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_use_case() -> GetUserUseCase:
    return GetUserUseCase(db_helper.async_session_maker)


def get_register_user_use_case() -> RegisterUserUseCase:
    return RegisterUserUseCase(lambda: UnitOfWork())


def get_update_user_use_case() -> UpdateUserUseCase:
    return UpdateUserUseCase(lambda: UnitOfWork())


def get_update_user_password_use_case() -> UpdateUserPasswordUseCase:
    return UpdateUserPasswordUseCase(lambda: UnitOfWork())


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_in: UserCreate,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
):
    command = RegisterUserCommand(
        username=user_in.username,
        email=str(user_in.email),
        password=user_in.password,
    )
    return await use_case.execute(command)


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    use_case: Annotated[GetUserUseCase, Depends(get_user_use_case)],
):
    query = GetUserQuery(user_id=current_user.sub)
    return await use_case.execute(query)


@router.patch("/me", response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    use_case: Annotated[UpdateUserUseCase, Depends(get_update_user_use_case)],
):
    command = UpdateUserCommand(
        user_id=current_user.sub,
        changes=user_update.model_dump(exclude_unset=True),
    )
    return await use_case.execute(command)


@router.patch("/me/password", response_model=UserRead)
async def update_user_password(
    password_update: UserPasswordUpdate,
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    use_case: Annotated[
        UpdateUserPasswordUseCase, Depends(get_update_user_password_use_case)
    ],
):
    command = UpdateUserPasswordCommand(
        user_id=current_user.sub,
        current_password=password_update.current_password,
        new_password=password_update.new_password,
    )
    return await use_case.execute(command)


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: int,
    use_case: Annotated[GetUserUseCase, Depends(get_user_use_case)],
    _: Annotated[UserPayload, Depends(get_current_user)],
):
    query = GetUserQuery(user_id=user_id)
    return await use_case.execute(query)


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
