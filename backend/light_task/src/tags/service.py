from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import db_helper
from src.tags.models import Tag
from src.realtimev1.dependencies import get_event_publisher
from src.realtimev1.publisher import DomainEventPublisher


class TagService:
    def __init__(self, session: AsyncSession, event_publisher: DomainEventPublisher):
        self.session = session
        self.event_publisher = event_publisher

    async def get_project_tags(
        self,
        project_id: int,
    ) -> Sequence[Tag]:
        query = select(Tag).where(Tag.project_id == project_id).order_by(Tag.name)
        result = await self.session.execute(query)
        return result.scalars().all()


def get_tag_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
    event_publisher: Annotated[DomainEventPublisher, Depends(get_event_publisher)],
) -> TagService:
    return TagService(session, event_publisher)
