from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db.database import db_helper
from src.auth import utils
from src.users.models import User


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
http_bearer = HTTPBearer()


async def get_user_from_token(
    token: str, required_type: str, session: AsyncSession
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = utils.decode_jwt(token)

    if not payload:
        raise credentials_exception

    token_type = payload.get("type")
    if token_type != required_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: expected {required_type}, got {token_type}",
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    query = select(User).where(User.id == int(user_id))
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return user


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(db_helper.get_async_session),
) -> User:
    return await get_user_from_token(
        creds.credentials, utils.ACCESS_TOKEN_TYPE, session
    )


async def get_current_user_for_refresh(
    creds: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: AsyncSession = Depends(db_helper.get_async_session),
) -> User:
    return await get_user_from_token(
        creds.credentials, utils.REFRESH_TOKEN_TYPE, session
    )
