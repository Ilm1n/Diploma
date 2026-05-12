from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class LoginCommand:
    username_or_email: str
    password: str


@dataclass(frozen=True, kw_only=True)
class RefreshTokenCommand:
    refresh_token: str | None


@dataclass(frozen=True, kw_only=True)
class TokenResult:
    access_token: str
    token_type: str
    refresh_token: str
