from typing import Annotated

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

import src.security as security
from src.auth.schemas import UserPayload
from src.logger import auth_logger
from src.errors import ErrorCode
from src.db.database import db_helper
from src.users.models import User

http_bearer = HTTPBearer(auto_error=False)


async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorCode.USER_NOT_FOUND
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=ErrorCode.INACTIVE_USER
        )
    return user


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> UserPayload:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.NOT_AUTHENTICATED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = security.decode_jwt(creds.credentials)

    if payload.get("type") != security.ACCESS_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_TOKEN_TYPE,
        )

    user_id = payload.get("sub")
    username = payload.get("username")
    email = payload.get("email")
    is_active = payload.get("is_active", True)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_TOKEN_PAYLOAD,
        )

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=ErrorCode.INACTIVE_USER
        )

    return UserPayload(
        sub=int(user_id),
        username=username,
        email=email,
        is_active=is_active,
    )


async def get_current_user_for_refresh(
    refresh_token: Annotated[str | None, Cookie()] = None,
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)] = None,
) -> User:
    if not refresh_token:
        auth_logger.warning("Refresh token missing in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.REFRESH_TOKEN_MISSING,
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = security.decode_jwt(refresh_token)

    if payload.get("type") != security.REFRESH_TOKEN_TYPE:
        auth_logger.warning("Invalid refresh token type")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_TOKEN_TYPE,
        )

    user_id = payload.get("sub")
    if not user_id:
        auth_logger.warning("Invalid refresh token payload - missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_TOKEN_PAYLOAD,
        )

    return await get_user_by_id(int(user_id), session)
