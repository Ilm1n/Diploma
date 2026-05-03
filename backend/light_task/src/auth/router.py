from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from src.auth import schemas
from src.auth.dependencies import get_current_user_for_refresh
from src.auth.service import AuthService, get_auth_service
from src.auth.yandex import (
    YandexAuthService,
    YandexOAuthError,
    get_yandex_auth_service,
)
from src.config import settings
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


@router.get("/yandex/start", include_in_schema=False)
async def start_yandex_auth(
    yandex_auth_service: Annotated[
        YandexAuthService,
        Depends(get_yandex_auth_service),
    ],
    next_path: Annotated[str | None, Query(alias="next")] = None,
) -> RedirectResponse:
    return yandex_auth_service.build_start_redirect(next_path)


@router.get("/yandex/callback", include_in_schema=False)
async def yandex_auth_callback(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    yandex_auth_service: Annotated[
        YandexAuthService,
        Depends(get_yandex_auth_service),
    ],
    code: str | None = None,
    state: str | None = None,
    state_cookie: Annotated[
        str | None,
        Cookie(alias=settings.yandex.state_cookie_name),
    ] = None,
) -> RedirectResponse:
    try:
        user, next_path = await yandex_auth_service.authenticate_callback(
            code=code,
            state=state,
            state_cookie=state_cookie,
        )
    except YandexOAuthError as exc:
        return yandex_auth_service.build_frontend_error_redirect(exc.code)

    response = yandex_auth_service.build_frontend_success_redirect(next_path)
    auth_service.set_tokens(user, response)
    return response


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
