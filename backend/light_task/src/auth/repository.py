from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_username_or_email(
        self, username_or_email: str
    ) -> User | None:
        stmt = select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_user(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)
