from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.auth import schemas
from src.auth.dependencies import get_current_user_for_refresh
from src.auth.service import AuthService, get_auth_service
from src.users.models import User

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/login",
    response_model=schemas.Token,
)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    user = await auth_service.authenticate_user(
        username_or_email=form_data.username,
        password=form_data.password,
    )
    return auth_service.set_tokens(user, response)


@router.post(
    "/refresh",
    response_model=schemas.Token,
)
async def refresh_jwt(
    response: Response,
    user: Annotated[User, Depends(get_current_user_for_refresh)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    return auth_service.set_tokens(user, response)


@router.post("/logout")
async def logout(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    auth_service.logout(response)
    return {"detail": "Logged out successfully"}