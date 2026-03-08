from typing import Annotated

from fastapi import HTTPException, status, Response, Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import Token
from src.logger import auth_logger
from src.errors import ErrorCode
from src.users.models import User
from src.db.database import db_helper
from src.config import settings
import src.security as security


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate_user(
        self,
        username_or_email: str,
        password: str,
    ) -> User:
        query = select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email)
        )
        user = (await self.session.execute(query)).scalar_one_or_none()

        if not user or not security.validate_password(password, user.hashed_password):
            auth_logger.warning(f"Failed login attempt for {username_or_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorCode.INVALID_CREDENTIALS,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def set_tokens(self, user: User, response: Response) -> Token:
        token_payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
        }

        access_token = security.create_access_token(
            user_data=token_payload,
        )

        refresh_token = security.create_refresh_token(
            user_id=user.id,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.auth_jwt.secure,
            samesite="lax",
            path="/",
            max_age=settings.auth_jwt.refresh_token_expire_days * 24 * 60 * 60,
        )

        auth_logger.info(f"Token issued for user {user.id}")
        return Token(
            access_token=access_token,
            token_type="bearer",
        )

    def logout(self, response: Response) -> None:
        response.delete_cookie(
            key="refresh_token",
            path="/",
            httponly=True,
            samesite="lax",
        )
        auth_logger.info("User logged out")


def get_auth_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> AuthService:
    return AuthService(session)
