from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.unit_of_work import UnitOfWork
from src.errors import ErrorCode
from src.logger import user_logger
from src.shared.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    DatabaseError,
    NotFoundError,
)
from src.users.dto import (
    GetUserQuery,
    RegisterUserCommand,
    UpdateUserCommand,
    UpdateUserPasswordCommand,
)
from src.users.models import User
from src.users.passwords import hash_password, validate_password
from src.users.repository import UserRepository


class GetUserUseCase:
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, query: GetUserQuery) -> User:
        try:
            async with self._session_factory() as session:
                repository = UserRepository(session)
                user = await repository.get_user(query.user_id)
                if user is None:
                    raise NotFoundError(ErrorCode.USER_NOT_FOUND)
                return user
        except AppError:
            raise
        except Exception as exc:
            user_logger.exception(
                "Failed to read user %s",
                query.user_id,
                exc_info=exc,
            )
            raise DatabaseError() from exc


class RegisterUserUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, command: RegisterUserCommand) -> User:
        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("UnitOfWork has not been entered")

                repository = UserRepository(uow.session)
                user = repository.add_user(
                    email=command.email,
                    username=command.username,
                    hashed_password=hash_password(command.password),
                )
                await repository.flush()
                await repository.refresh_user(user)
                return user
        except IntegrityError as exc:
            user_logger.warning("Failed to create user - username/email already exists")
            raise ConflictError(ErrorCode.USERNAME_OR_EMAIL_EXISTS) from exc
        except AppError:
            raise
        except Exception as exc:
            user_logger.exception(
                "Failed to create user %s",
                command.username,
                exc_info=exc,
            )
            raise DatabaseError() from exc


class UpdateUserUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, command: UpdateUserCommand) -> User:
        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("UnitOfWork has not been entered")

                repository = UserRepository(uow.session)
                user = await repository.get_user(command.user_id)
                if user is None:
                    raise NotFoundError(ErrorCode.USER_NOT_FOUND)

                if not command.changes:
                    return user

                for key, value in command.changes.items():
                    setattr(user, key, value)

                repository.save_user(user)
                await repository.flush()
                await repository.refresh_user(user)
                return user
        except IntegrityError as exc:
            user_logger.warning("Failed to update user - username already taken")
            raise ConflictError(ErrorCode.USERNAME_TAKEN) from exc
        except AppError:
            raise
        except Exception as exc:
            user_logger.exception(
                "Failed to update user %s",
                command.user_id,
                exc_info=exc,
            )
            raise DatabaseError() from exc


class UpdateUserPasswordUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, command: UpdateUserPasswordCommand) -> User:
        try:
            async with self._uow_factory() as uow:
                if uow.session is None:
                    raise RuntimeError("UnitOfWork has not been entered")

                repository = UserRepository(uow.session)
                user = await repository.get_user(command.user_id)
                if user is None:
                    raise NotFoundError(ErrorCode.USER_NOT_FOUND)

                if user.hashed_password:
                    if not command.current_password:
                        raise BadRequestError(ErrorCode.CURRENT_PASSWORD_REQUIRED)
                    if not validate_password(
                        command.current_password,
                        user.hashed_password,
                    ):
                        raise BadRequestError(ErrorCode.INVALID_CURRENT_PASSWORD)

                user.hashed_password = hash_password(command.new_password)
                repository.save_user(user)
                await repository.flush()
                await repository.refresh_user(user)
                return user
        except AppError:
            raise
        except Exception as exc:
            user_logger.exception(
                "Failed to update password for user %s",
                command.user_id,
                exc_info=exc,
            )
            raise DatabaseError() from exc
