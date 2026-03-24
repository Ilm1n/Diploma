from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.auth.schemas import UserPayload
from src.projects.dependencies import check_project_manager, check_project_member
from src.realtimev1.dependencies import get_client_mutation_id
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
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    return await tag_service.create_tag(
        project_id,
        tag_in,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.patch("/tags/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_update: TagUpdate,
    tag: Annotated[Tag, Depends(get_tag_for_write)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    return await tag_service.update_tag(
        tag,
        tag_update,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag: Annotated[Tag, Depends(get_tag_for_write)],
    current_user: Annotated[UserPayload, Depends(get_current_user)],
    tag_service: Annotated[TagService, Depends(get_tag_service)],
    client_mutation_id: Annotated[str | None, Depends(get_client_mutation_id)],
):
    await tag_service.delete_tag(
        tag,
        actor_user_id=current_user.sub,
        client_mutation_id=client_mutation_id,
    )
