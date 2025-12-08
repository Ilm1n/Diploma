from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth.dependencies import get_current_user_for_refresh
from src.core.db.database import db_helper
from src.users.models import User
from src.users.schemas import UserCreate, UserRead
from src.auth import utils, security, schemas


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    hashed_pw = security.hash_password(user_in.password)

    new_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_pw,
    )

    session.add(new_user)

    try:
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    return new_user


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(db_helper.get_async_session),
):
    query = select(User).where(
        (User.username == form_data.username) | (User.email == form_data.username)
    )

    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user or not security.validate_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = utils.create_access_token(
        user.id,
        user.username,
        user.email,
    )
    refresh_token = utils.create_refresh_token(
        user.id,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Token)
async def refresh_jwt(user: User = Depends(get_current_user_for_refresh)):
    access_token = utils.create_access_token(user.id, user.username, user.email)
    new_refresh_token = utils.create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
