from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import db_helper
from src.errors import ErrorCode
from src.logger import auth_logger
from src.users.models import User

DEFAULT_NEXT_PATH = "/projects"
FRONTEND_CALLBACK_PATH = "/auth/yandex/callback"


@dataclass(frozen=True)
class YandexProfile:
    yandex_id: str
    email: str
    username: str
    full_name: str | None


class YandexOAuthError(Exception):
    def __init__(self, code: str):
        self.code = code


class YandexAuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def build_start_redirect(self, next_path: str | None) -> RedirectResponse:
        self._ensure_configured()

        safe_next = self._safe_next_path(next_path)
        state = secrets.token_urlsafe(32)
        cookie_value = f"{state}|{safe_next}"

        url = f"{settings.yandex.authorize_url}?{urlencode({
            'response_type': 'code',
            'client_id': settings.yandex.client_id,
            'redirect_uri': settings.yandex.redirect_uri,
            'state': state,
        })}"

        response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key=settings.yandex.state_cookie_name,
            value=cookie_value,
            httponly=True,
            secure=settings.auth_jwt.secure,
            samesite="lax",
            path="/api/auth/yandex",
            max_age=settings.yandex.state_cookie_max_age_seconds,
        )
        return response

    async def authenticate_callback(
        self,
        code: str | None,
        state: str | None,
        state_cookie: str | None,
    ) -> tuple[User, str]:
        self._ensure_configured()
        next_path = self._validate_state(state=state, state_cookie=state_cookie)

        if not code:
            raise YandexOAuthError("missing_code")

        access_token = await self._exchange_code_for_token(code)
        profile = await self._fetch_profile(access_token)
        user = await self._get_or_create_user(profile)
        return user, next_path

    def build_frontend_success_redirect(self, next_path: str) -> RedirectResponse:
        safe_next = self._safe_next_path(next_path)
        url = self._frontend_url(
            FRONTEND_CALLBACK_PATH,
            {"next": safe_next},
        )
        response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        self.clear_state_cookie(response)
        return response

    def build_frontend_error_redirect(self, error_code: str) -> RedirectResponse:
        url = self._frontend_url(
            "/login",
            {"oauth_error": error_code},
        )
        response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        self.clear_state_cookie(response)
        return response

    def clear_state_cookie(self, response: RedirectResponse) -> None:
        response.delete_cookie(
            key=settings.yandex.state_cookie_name,
            path="/api/auth/yandex",
            httponly=True,
            samesite="lax",
        )

    async def _exchange_code_for_token(self, code: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    settings.yandex.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": settings.yandex.client_id,
                        "client_secret": settings.yandex.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except httpx.HTTPError:
            auth_logger.exception("Yandex token request failed")
            raise YandexOAuthError("token_request_failed")

        if response.status_code != status.HTTP_200_OK:
            auth_logger.warning("Yandex token exchange failed: %s", response.text)
            raise YandexOAuthError("invalid_code")

        token_data = response.json()
        access_token = token_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise YandexOAuthError("missing_yandex_token")
        return access_token

    async def _fetch_profile(self, access_token: str) -> YandexProfile:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    settings.yandex.userinfo_url,
                    params={"format": "json"},
                    headers={"Authorization": f"OAuth {access_token}"},
                )
        except httpx.HTTPError:
            auth_logger.exception("Yandex profile request failed")
            raise YandexOAuthError("profile_request_failed")

        if response.status_code != status.HTTP_200_OK:
            auth_logger.warning("Yandex profile request failed: %s", response.text)
            raise YandexOAuthError("profile_request_failed")

        return self._parse_profile(response.json())

    def _parse_profile(self, data: dict[str, Any]) -> YandexProfile:
        yandex_id = str(data.get("id") or "").strip()
        email = str(data.get("default_email") or "").strip().lower()

        if not yandex_id:
            raise YandexOAuthError("missing_yandex_id")
        if not email:
            raise YandexOAuthError("missing_email")

        username = self._normalize_username(
            data.get("login") or data.get("display_name") or email.split("@", 1)[0]
        )
        full_name = data.get("real_name") or data.get("display_name")
        if isinstance(full_name, str):
            full_name = full_name.strip() or None
        else:
            full_name = None

        return YandexProfile(
            yandex_id=yandex_id,
            email=email,
            username=username,
            full_name=full_name,
        )

    async def _get_or_create_user(self, profile: YandexProfile) -> User:
        user = await self._get_user_by_yandex_id(profile.yandex_id)
        if user:
            return user

        user = await self._get_user_by_email(profile.email)
        if user:
            if user.yandex_id and user.yandex_id != profile.yandex_id:
                raise YandexOAuthError("email_already_linked")
            user.yandex_id = profile.yandex_id
            if not user.full_name and profile.full_name:
                user.full_name = profile.full_name
            return await self._commit_user(user)

        username = await self._build_unique_username(profile.username)
        user = User(
            email=profile.email,
            username=username,
            full_name=profile.full_name,
            hashed_password=None,
            yandex_id=profile.yandex_id,
        )
        self.session.add(user)
        return await self._commit_user(user)

    async def _commit_user(self, user: User) -> User:
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError:
            await self.session.rollback()
            auth_logger.exception("Failed to save Yandex user")
            raise YandexOAuthError("account_save_failed")

    async def _get_user_by_yandex_id(self, yandex_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.yandex_id == yandex_id)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _build_unique_username(self, base_username: str) -> str:
        base = base_username[:50]
        username = base
        suffix = 1

        while await self._username_exists(username):
            suffix_text = f"_{suffix}"
            username = f"{base[: 50 - len(suffix_text)]}{suffix_text}"
            suffix += 1

        return username

    async def _username_exists(self, username: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None

    def _validate_state(self, state: str | None, state_cookie: str | None) -> str:
        if not state or not state_cookie:
            raise YandexOAuthError("invalid_state")

        cookie_state, separator, next_path = state_cookie.partition("|")
        if not separator or not secrets.compare_digest(cookie_state, state):
            raise YandexOAuthError("invalid_state")

        return self._safe_next_path(next_path)

    def _safe_next_path(self, next_path: str | None) -> str:
        if not next_path:
            return DEFAULT_NEXT_PATH
        if not next_path.startswith("/") or next_path.startswith("//"):
            return DEFAULT_NEXT_PATH
        return next_path

    def _frontend_url(self, path: str, query: dict[str, str]) -> str:
        base_url = settings.frontend.base_url.rstrip("/")
        return f"{base_url}{path}?{urlencode(query)}"

    def _normalize_username(self, value: Any) -> str:
        username = str(value or "").strip().lower()
        username = re.sub(r"[^a-z0-9_]+", "_", username)
        username = re.sub(r"_+", "_", username).strip("_")
        return username[:50] or "yandex_user"

    def _ensure_configured(self) -> None:
        if settings.yandex.client_id and settings.yandex.client_secret:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorCode.UNKNOWN_ERROR,
        )


def get_yandex_auth_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> YandexAuthService:
    return YandexAuthService(session)
