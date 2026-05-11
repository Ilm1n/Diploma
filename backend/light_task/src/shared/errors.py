from __future__ import annotations

from typing import Any

from src.errors import ErrorCode


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode | str,
        *,
        status_code: int,
        params: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.params = params
        super().__init__(str(code))


class BadRequestError(AppError):
    def __init__(
        self,
        code: ErrorCode | str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, status_code=400, params=params)


class UnauthorizedError(AppError):
    def __init__(
        self,
        code: ErrorCode | str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, status_code=401, params=params)


class ForbiddenError(AppError):
    def __init__(
        self,
        code: ErrorCode | str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, status_code=403, params=params)


class NotFoundError(AppError):
    def __init__(
        self,
        code: ErrorCode | str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, status_code=404, params=params)


class ConflictError(AppError):
    def __init__(
        self,
        code: ErrorCode | str,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, status_code=409, params=params)


class DatabaseError(AppError):
    def __init__(
        self,
        code: ErrorCode | str = ErrorCode.DATABASE_ERROR,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, status_code=500, params=params)
