from fastapi import APIRouter, Depends

from src.users.schemas import UserRead
from src.users.models import User
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
