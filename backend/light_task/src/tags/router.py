from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.projects.dependencies import check_project_manager, check_project_member
from src.tags.dependencies import get_tag_for_write
from src.tags.models import Tag
from src.tags.schemas import TagCreate, TagRead, TagUpdate
from src.tags.service import TagService, get_tag_service

router = APIRouter(tags=["Tags"])


@router.get("/projects/{project_id}/tags", response_model=list[TagRead])
async def get_project_tags(
    project_id: int,
    _: Annotated[None, Depends(check_project_member)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
):
    return await tag_service.get_project_tags(project_id)


@router.post(
    "/projects/{project_id}/tags",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    project_id: int,
    tag_in: TagCreate,
    _: Annotated[None, Depends(check_project_manager)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
):
    return await tag_service.create_tag(project_id, tag_in)


@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_update: TagUpdate,
    tag: Annotated[Tag, Depends(get_tag_for_write)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
):
    return await tag_service.update_tag(tag, tag_update)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag: Annotated[Tag, Depends(get_tag_for_write)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
):
    await tag_service.delete_tag(tag)
