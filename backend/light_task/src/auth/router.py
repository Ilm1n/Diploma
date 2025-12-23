from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from light_task.src.auth import schemas
from light_task.src.auth.dependencies import get_current_user_for_refresh
from light_task.src.auth.service import AuthService
from light_task.src.db.database import db_helper
from light_task.src.users.models import User

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    response_model=schemas.Token,
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await AuthService.authenticate_user(
        session=session,
        username_or_email=form_data.username,
        password=form_data.password,
    )


@router.post(
    "/refresh",
    response_model=schemas.Token,
)
async def refresh_jwt(
    user: Annotated[User, Depends(get_current_user_for_refresh)],
):
    return AuthService.refresh_tokens(user)
