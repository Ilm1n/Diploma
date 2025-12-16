from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import db_helper
from src.projects.dependencies import require_project_manager, require_project_member
from src.projects.models import Project
from src.tags.dependencies import get_tag_for_write
from src.tags.models import Tag
from src.tags.schemas import TagCreate, TagRead, TagUpdate
from src.tags.service import TagService

router = APIRouter(tags=["Tags"])


@router.get("/projects/{project_id}/tags", response_model=list[TagRead])
async def get_project_tags(
    project_id: int,
    _: Annotated[Project, Depends(require_project_member)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await TagService.get_project_tags(session, project_id)


@router.post(
    "/projects/{project_id}/tags",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    project_id: int,
    tag_in: TagCreate,
    _: Annotated[Project, Depends(require_project_manager)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await TagService.create_tag(session, project_id, tag_in)


@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    tag: Annotated[Tag, Depends(get_tag_for_write)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    return await TagService.update_tag(session, tag, tag_update)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    tag: Annotated[Tag, Depends(get_tag_for_write)],
    session: Annotated[AsyncSession, Depends(db_helper.get_async_session)],
):
    await TagService.delete_tag(session, tag)
