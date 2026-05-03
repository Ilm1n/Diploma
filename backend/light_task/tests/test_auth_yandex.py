from __future__ import annotations

import asyncio
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import select

from src.auth.yandex import YandexAuthService, YandexOAuthError, YandexProfile
from src.db.database import db_helper
from src.security import hash_password
from src.users.models import User

PASSWORD = "VeryStrongPass123!"


def _state_from_start_response(client: TestClient, next_path: str = "/projects") -> str:
    response = client.get(
        "/api/auth/yandex/start",
        params={"next": next_path},
        follow_redirects=False,
    )
    assert response.status_code == 302, response.text

    location = response.headers["location"]
    query = parse_qs(urlparse(location).query)
    return query["state"][0]


async def _fake_exchange_code_for_token(self: YandexAuthService, code: str) -> str:
    if code == "bad-code":
        raise YandexOAuthError("invalid_code")
    return "yandex-access-token"


async def _fake_fetch_profile(
    self: YandexAuthService,
    access_token: str,
) -> YandexProfile:
    return YandexProfile(
        yandex_id="yandex-123",
        email="yandex-user@example.com",
        username="ivan",
        full_name="Ivan Ivanov",
    )


async def _fake_fetch_profile_without_email(
    self: YandexAuthService,
    access_token: str,
) -> YandexProfile:
    raise YandexOAuthError("missing_email")


def _patch_yandex_success(monkeypatch) -> None:
    monkeypatch.setattr(
        YandexAuthService,
        "_exchange_code_for_token",
        _fake_exchange_code_for_token,
    )
    monkeypatch.setattr(
        YandexAuthService,
        "_fetch_profile",
        _fake_fetch_profile,
    )


async def _get_user_by_email(email: str) -> User | None:
    async with db_helper.async_session_maker() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def _create_local_user(
    *,
    username: str,
    email: str,
    yandex_id: str | None = None,
) -> User:
    async with db_helper.async_session_maker() as session:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(PASSWORD),
            yandex_id=yandex_id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def test_yandex_callback_creates_new_user(client: TestClient, monkeypatch) -> None:
    _patch_yandex_success(monkeypatch)
    state = _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    assert response.headers["location"] == (
        "http://localhost:5173/auth/yandex/callback?next=%2Fprojects"
    )

    cookies = SimpleCookie(response.headers["set-cookie"])
    assert "refresh_token" in cookies

    user = asyncio.run(_get_user_by_email("yandex-user@example.com"))
    assert user is not None
    assert user.yandex_id == "yandex-123"
    assert user.username == "ivan"
    assert user.hashed_password is None


def test_yandex_callback_auto_links_existing_user_by_email(
    client: TestClient,
    monkeypatch,
) -> None:
    _patch_yandex_success(monkeypatch)
    local_user = asyncio.run(
        _create_local_user(
            username="existing",
            email="yandex-user@example.com",
        )
    )
    state = _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    user = asyncio.run(_get_user_by_email("yandex-user@example.com"))
    assert user is not None
    assert user.id == local_user.id
    assert user.yandex_id == "yandex-123"
    assert user.hashed_password is not None


def test_yandex_callback_uses_linked_user_by_yandex_id(
    client: TestClient,
    monkeypatch,
) -> None:
    _patch_yandex_success(monkeypatch)
    linked_user = asyncio.run(
        _create_local_user(
            username="linked",
            email="different@example.com",
            yandex_id="yandex-123",
        )
    )
    state = _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    user = asyncio.run(_get_user_by_email("different@example.com"))
    assert user is not None
    assert user.id == linked_user.id


def test_yandex_callback_adds_suffix_when_username_is_taken(
    client: TestClient,
    monkeypatch,
) -> None:
    _patch_yandex_success(monkeypatch)
    asyncio.run(
        _create_local_user(
            username="ivan",
            email="ivan-local@example.com",
        )
    )
    state = _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    user = asyncio.run(_get_user_by_email("yandex-user@example.com"))
    assert user is not None
    assert user.username == "ivan_1"


def test_yandex_callback_rejects_invalid_state(
    client: TestClient,
    monkeypatch,
) -> None:
    _patch_yandex_success(monkeypatch)
    _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "valid-code", "state": "wrong-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    assert response.headers["location"] == (
        "http://localhost:5173/login?oauth_error=invalid_state"
    )


def test_yandex_callback_handles_invalid_code(
    client: TestClient,
    monkeypatch,
) -> None:
    _patch_yandex_success(monkeypatch)
    state = _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "bad-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    assert response.headers["location"] == (
        "http://localhost:5173/login?oauth_error=invalid_code"
    )


def test_yandex_callback_requires_email(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(
        YandexAuthService,
        "_exchange_code_for_token",
        _fake_exchange_code_for_token,
    )
    monkeypatch.setattr(
        YandexAuthService,
        "_fetch_profile",
        _fake_fetch_profile_without_email,
    )
    state = _state_from_start_response(client)

    response = client.get(
        "/api/auth/yandex/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    assert response.headers["location"] == (
        "http://localhost:5173/login?oauth_error=missing_email"
    )


def test_password_login_still_works(client: TestClient) -> None:
    response = client.post(
        "/api/users/register",
        json={
            "username": "password_user",
            "email": "password-user@example.com",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/auth/login",
        data={
            "username": "password_user",
            "password": PASSWORD,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["accessToken"]
