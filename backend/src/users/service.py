import shutil
import uuid

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import src.core.security as security
from src.config import settings
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
        session: AsyncSession, user: User, file: UploadFile
    ) -> User:
        if user.avatar_url:
            url_prefix = f"{settings.files.static_url}/avatars/"

            if user.avatar_url.startswith(url_prefix):
                filename = user.avatar_url.replace(url_prefix, "")

                old_file_path = settings.files.avatars_dir / filename

                try:
                    old_file_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Failed to delete old avatar: {e}")

        extension = file.filename.split(".")[-1].lower()
        if extension not in ["jpg", "jpeg", "png", "webp"]:
            extension = "jpg"

        file_name = f"user_{user.id}_{uuid.uuid4()}.{extension}"

        destination_path = settings.files.avatars_dir / file_name

        try:
            with destination_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            await file.close()

        public_url = f"{settings.files.static_url}/avatars/{file_name}"

        user.avatar_url = public_url
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user
