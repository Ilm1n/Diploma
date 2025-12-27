from sqlalchemy import update, func
from sqlalchemy.ext.asyncio import AsyncSession


from src.projects.models import Project
from src.boards.models import Task


async def touch_project(
   session: AsyncSession,
   project_id: int,
) -> None:
   await session.execute(
       update(Project)
       .where(Project.id == project_id)
       .values(updated_at=func.now())
   )




async def touch_task(
   session: AsyncSession,
   task_id: int,
) -> None:
   await session.execute(
       update(Task)
       .where(Task.id == task_id)
       .values(updated_at=func.now())
   )
