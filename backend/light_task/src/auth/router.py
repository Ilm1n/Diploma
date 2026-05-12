from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from src.auth import schemas
from src.auth.dto import LoginCommand, RefreshTokenCommand
from src.auth.tokens import (
    apply_refresh_cookie,
    clear_refresh_cookie,
    create_token_result,
    token_response,
)
from src.auth.use_cases import LoginUseCase, RefreshTokenUseCase
from src.auth.yandex import (
    YandexAuthService,
    YandexOAuthError,
    get_yandex_auth_service,
)
from src.config import settings
from src.db.database import db_helper

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(db_helper.async_session_maker)


def get_refresh_token_use_case() -> RefreshTokenUseCase:
    return RefreshTokenUseCase(db_helper.async_session_maker)


@router.post(
    "/login",
    response_model=schemas.Token,
)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: Annotated[LoginUseCase, Depends(get_login_use_case)],
):
    command = LoginCommand(
        username_or_email=form_data.username,
        password=form_data.password,
    )
    result = await use_case.execute(command)
    apply_refresh_cookie(response, result.refresh_token)
    return token_response(result)


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
    result = create_token_result(user)
    apply_refresh_cookie(response, result.refresh_token)
    return response


@router.post(
    "/refresh",
    response_model=schemas.Token,
)
async def refresh_jwt(
    response: Response,
    use_case: Annotated[RefreshTokenUseCase, Depends(get_refresh_token_use_case)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    command = RefreshTokenCommand(refresh_token=refresh_token)
    result = await use_case.execute(command)
    apply_refresh_cookie(response, result.refresh_token)
    return token_response(result)


@router.post("/logout")
async def logout(
    response: Response,
):
    clear_refresh_cookie(response)
    return {"detail": "Logged out successfully"}
