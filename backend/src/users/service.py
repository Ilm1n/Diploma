from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import src.core.security as security
from src.users.models import User
from src.users.schemas import UserCreate


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
