from collections.abc import Sequence
from typing import Annotated

from fastapi import HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import db_helper
from src.logger import board_logger
from src.errors import ErrorCode
from src.tags.models import Tag
from src.tags.schemas import TagCreate, TagUpdate


class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_project_tags(
        self,
        project_id: int,
    ) -> Sequence[Tag]:
        query = select(Tag).where(Tag.project_id == project_id).order_by(Tag.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_tag(
        self,
        project_id: int,
        data: TagCreate,
    ) -> Tag:
        query = select(Tag).where(
            Tag.project_id == project_id,
            Tag.name == data.name,
        )
        existing = await self.session.scalar(query)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.TAG_ALREADY_EXISTS,
            )

        tag = Tag(
            name=data.name,
            color=data.color,
            project_id=project_id,
        )
        self.session.add(tag)
        try:
            await self.session.commit()
            await self.session.refresh(tag)
            board_logger.info(f"Tag created: {tag.id} in project {project_id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to create tag in project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )
        return tag

    async def update_tag(
        self,
        tag: Tag,
        data: TagUpdate,
    ) -> Tag:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tag, key, value)

        self.session.add(tag)
        try:
            await self.session.commit()
            await self.session.refresh(tag)
            return tag
        except Exception:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.TAG_ALREADY_EXISTS,
            )

    async def delete_tag(
        self,
        tag: Tag,
    ) -> None:
        await self.session.delete(tag)
        try:
            await self.session.commit()
            board_logger.info(f"Tag deleted: {tag.id}")
        except Exception as e:
            await self.session.rollback()
            board_logger.exception(f"Failed to delete tag {tag.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.DATABASE_ERROR,
            )


def get_tag_service(
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
) -> TagService:
    return TagService(session)
