from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

import light_task.src.security as security
from light_task.src.db.database import db_helper
from light_task.src.users.models import User

http_bearer = HTTPBearer(auto_error=False)


async def get_user_from_token(
    token: str,
    required_type: str,
    session: AsyncSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.decode_jwt(token)

    if not payload:
        raise credentials_exception

    token_type = payload.get("type")
    if token_type != required_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: expected {required_type}, got {token_type}",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await session.get(User, int(user_id))

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> User:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_user_from_token(
        creds.credentials,
        security.ACCESS_TOKEN_TYPE,
        session,
    )


async def get_current_user_for_refresh(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> User:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_user_from_token(
        creds.credentials,
        security.REFRESH_TOKEN_TYPE,
        session,
    )
