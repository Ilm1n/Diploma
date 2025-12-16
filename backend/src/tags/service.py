from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.tags.models import Tag
from src.tags.schemas import TagCreate, TagUpdate


class TagService:
    @staticmethod
    async def get_project_tags(
        session: AsyncSession,
        project_id: int,
    ) -> Sequence[Tag]:
        query = select(Tag).where(Tag.project_id == project_id).order_by(Tag.name)
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_tag(
        session: AsyncSession,
        project_id: int,
        data: TagCreate,
    ) -> Tag:
        query = select(Tag).where(
            Tag.project_id == project_id,
            Tag.name == data.name,
        )
        existing = await session.scalar(query)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tag with this name already exists in the project",
            )

        tag = Tag(
            name=data.name,
            color=data.color,
            project_id=project_id,
        )
        session.add(tag)
        await session.commit()
        await session.refresh(tag)
        return tag

    @staticmethod
    async def update_tag(
        session: AsyncSession,
        tag: Tag,
        data: TagUpdate,
    ) -> Tag:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tag, key, value)

        session.add(tag)
        try:
            await session.commit()
            await session.refresh(tag)
            return tag
        except Exception:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tag with this name already exists",
            )

    @staticmethod
    async def delete_tag(
        session: AsyncSession,
        tag: Tag,
    ) -> None:
        await session.delete(tag)
        await session.commit()
