import uuid
from urllib.parse import urlparse
from typing import Annotated

from fastapi import HTTPException, status, BackgroundTasks, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import src.security as security
from src.config import settings
from src.db.database import db_helper
from src.logger import user_logger
from src.errors import ErrorCode
from src.s3 import S3Client
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_in: UserCreate) -> User:
        hashed_password = security.hash_password(user_in.password)

        new_user = User(
            email=str(user_in.email),
            username=user_in.username,
            hashed_password=hashed_password,
        )

        self.session.add(new_user)

        try:
            await self.session.commit()
            await self.session.refresh(new_user)
            user_logger.info(f"User created successfully: {new_user.username}")
            return new_user
        except IntegrityError:
            await self.session.rollback()
            user_logger.warning(
                f"Failed to create user - username/email already exists"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.USERNAME_OR_EMAIL_EXISTS,
            )

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.USER_NOT_FOUND,
            )
        return user

    async def update_user(
        self,
        user: User,
        user_update: UserUpdate,
    ) -> User:
        update_data = user_update.model_dump(exclude_unset=True)

        if not update_data:
            return user

        for key, value in update_data.items():
            setattr(user, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(user)
            user_logger.info(f"User updated successfully: {user.username}")
            return user
        except IntegrityError:
            await self.session.rollback()
            user_logger.warning(f"Failed to update user - username already taken")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.USERNAME_TAKEN,
            )

    async def upload_avatar(
        self,
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
                detail=ErrorCode.FILE_UPLOAD_FAILED,
            )

        user.avatar_url = public_url
        self.session.add(user)

        try:
            await self.session.commit()
            await self.session.refresh(user)
            user_logger.info(f"Avatar uploaded for user {user.id}")
        except Exception as e:
            await self.session.rollback()
            await s3_client.delete_file(object_name)
            user_logger.exception(f"Failed to commit avatar upload for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DB_COMMIT_FAILED,
            )

        if old_avatar_url:
            self._schedule_old_avatar_deletion(
                old_avatar_url, background_tasks, s3_client
            )

        return user

    async def delete_avatar(
        self,
        user: User,
        s3_client: S3Client,
        background_tasks: BackgroundTasks,
    ) -> User:
        if not user.avatar_url:
            return user

        old_avatar_url = user.avatar_url

        user.avatar_url = None
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        self._schedule_old_avatar_deletion(old_avatar_url, background_tasks, s3_client)

        return user

    def _schedule_old_avatar_deletion(
        self,
        url: str,
        bg_tasks: BackgroundTasks,
        s3_client: S3Client,
    ):
        try:
            parsed = urlparse(url)
            path = parsed.path.lstrip("/")
            if (
                settings.s3.bucket_name in path
                or settings.s3.bucket_name in parsed.netloc
            ):
                if path.startswith(settings.s3.bucket_name):
                    key = path.replace(f"{settings.s3.bucket_name}/", "", 1)
                    bg_tasks.add_task(s3_client.delete_file, key)
        except Exception as e:
            user_logger.exception(f"Failed to schedule old avatar deletion for {url}")


def get_user_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> UserService:
    return UserService(session)
