from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.boards.models import BoardColumn, Task
from src.db.database import db_helper
from src.tags.models import Tag


class BoardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_board(
        self,
        project_id: int,
    ) -> Sequence[BoardColumn]:
        stmt = (
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(BoardColumn.position.asc())
            .options(selectinload(BoardColumn.tasks).selectinload(Task.tags))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_project_tasks(
        self,
        project_id: int,
        assignee_id: int | None = None,
        tag_ids: list[int] | None = None,
        search: str | None = None,
    ) -> Sequence[Task]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .options(selectinload(Task.tags), selectinload(Task.assignee))
            .order_by(Task.updated_at.desc())
        )

        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)

        if search:
            stmt = stmt.where(
                or_(
                    Task.title.ilike(f"%{search}%"),
                    Task.description.ilike(f"%{search}%"),
                )
            )

        if tag_ids:
            stmt = stmt.join(Task.tags).where(Tag.id.in_(tag_ids)).distinct()

        result = await self.session.execute(stmt)
        return result.scalars().all()


def get_board_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> BoardService:
    return BoardService(session)
