import uuid
from urllib.parse import urlparse

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import light_task.src.security as security
from src.config import settings
from src.s3 import S3Client
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate


class UserService:
    @staticmethod
    async def create_user(
        session: AsyncSession,
        user_in: UserCreate,
    ) -> User:
        hashed_password = security.hash_password(user_in.password)

        new_user = User(
            email=str(user_in.email),
            username=user_in.username,
            hashed_password=hashed_password,
        )

        session.add(new_user)

        try:
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists",
            )

    @staticmethod
    async def get_user_by_id(
        session: AsyncSession,
        user_id: int,
    ) -> User:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user: User,
        user_update: UserUpdate,
    ) -> User:
        update_data = user_update.model_dump(exclude_unset=True)

        if not update_data:
            return user

        for key, value in update_data.items():
            setattr(user, key, value)

        try:
            await session.commit()
            await session.refresh(user)
            return user
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    @staticmethod
    async def upload_avatar(
        session: AsyncSession,
        user: User,
        file_data: bytes,
        extension: str,
        mime_type: str,
        s3_client: S3Client,
        background_tasks: BackgroundTasks,
    ) -> User:
        old_avatar_url = user.avatar_url
        object_name = f"avatars/user_{user.id}_{uuid.uuid4()}.{extension}"

        try:
            public_url = await s3_client.upload_file(
                file_data=file_data,
                object_name=object_name,
                content_type=mime_type,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File upload failed",
            )

        user.avatar_url = public_url
        session.add(user)

        try:
            await session.commit()
            await session.refresh(user)
        except Exception:
            await session.rollback()
            await s3_client.delete_file(object_name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database commit failed",
            )

        if old_avatar_url:
            UserService._schedule_old_avatar_deletion(
                old_avatar_url, background_tasks, s3_client
            )

        return user

    @staticmethod
    def _schedule_old_avatar_deletion(
        url: str,
        bg_tasks: BackgroundTasks,
        s3_client: S3Client,
    ):
        try:
            parsed = urlparse(url)
            path = parsed.path.lstrip("/")
            if path.startswith(settings.s3.bucket_name):
                key = path.replace(f"{settings.s3.bucket_name}/", "", 1)
                bg_tasks.add_task(s3_client.delete_file, key)
        except Exception as e:
            print(f"Failed to schedule old avatar deletion: {e}")
