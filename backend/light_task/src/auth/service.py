from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import Token
from src.users.models import User
import src.security as security


class AuthService:
    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        username_or_email: str,
        password: str,
    ) -> Token:
        query = select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email)
        )
        user = (await session.execute(query)).scalar_one_or_none()

        if not user or not security.validate_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthService._generate_token_response(user)

    @staticmethod
    def refresh_tokens(user: User) -> Token:
        return AuthService._generate_token_response(user)

    @staticmethod
    def _generate_token_response(user: User) -> Token:
        access_token = security.create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
        )
        refresh_token = security.create_refresh_token(
            user_id=user.id,
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
