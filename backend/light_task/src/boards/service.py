from collections.abc import Sequence
from datetime import datetime, timezone


from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes, selectinload


from src.boards.models import BoardColumn, Task
from src.boards.schemas import (
   ColumnCreate,
   TaskCreate,
   TaskMove,
   TaskUpdate,
   ColumnReorderRequest,
   ColumnUpdate,
)
from src.common.touch import touch_project
from src.projects.models import ProjectMember
from src.tags.models import Tag


POSITION_GAP = 65536.0
MIN_POSITION_DELTA = 0.0000001




class BoardService:
   @staticmethod
   async def get_board(
           session: AsyncSession,
           project_id: int,
   ) -> Sequence[BoardColumn]:
       stmt = (
           select(BoardColumn)
           .where(BoardColumn.project_id == project_id)
           .order_by(BoardColumn.position.asc())
           .options(selectinload(BoardColumn.tasks).selectinload(Task.tags))
       )
       result = await session.execute(stmt)
       return result.scalars().all()


   @staticmethod
   async def _check_column_limit(session: AsyncSession, column_id: int):
       column = await session.get(BoardColumn, column_id)
       if not column:
           raise HTTPException(status_code=404, detail="Column not found")


       if column.tasks_limit is not None:
           count_query = (
               select(func.count())
               .select_from(Task)
               .where(Task.column_id == column_id)
           )
           current_count = await session.scalar(count_query)


           if current_count >= column.tasks_limit:
               raise HTTPException(
                   status_code=status.HTTP_409_CONFLICT,
                   detail=f"Column '{column.name}' has reached its task limit ({column.tasks_limit})",
               )


   @staticmethod
   async def create_column(
           session: AsyncSession,
           project_id: int,
           data: ColumnCreate,
   ) -> BoardColumn:
       query = select(func.max(BoardColumn.position)).where(
           BoardColumn.project_id == project_id
       )
       max_pos = await session.scalar(query) or 0.0


       new_column = BoardColumn(
           name=data.name,
           tasks_limit=data.tasks_limit,
           project_id=project_id,
           position=max_pos + POSITION_GAP,
       )
       session.add(new_column)
       await touch_project(session, project_id)
       await session.commit()
       attributes.set_committed_value(new_column, "tasks", [])
       return new_column


   @staticmethod
   async def update_column(
           session: AsyncSession,
           column: BoardColumn,
           data: ColumnUpdate,
   ) -> BoardColumn:
       update_data = data.model_dump(exclude_unset=True)
       for key, value in update_data.items():
           setattr(column, key, value)


       session.add(column)
       await touch_project(session, column.project_id)
       await session.commit()
       return column


   @staticmethod
   async def delete_column(
           session: AsyncSession,
           column: BoardColumn,
   ) -> None:
       await session.delete(column)
       await touch_project(session, column.project_id)
       await session.commit()


   @staticmethod
   async def reorder_columns(
           session: AsyncSession,
           project_id: int,
           data: ColumnReorderRequest,
   ) -> None:
       stmt = select(BoardColumn).where(
           BoardColumn.project_id == project_id,
           BoardColumn.id.in_(data.column_ids),
       )
       result = await session.execute(stmt)
       columns = result.scalars().all()


       col_map = {col.id: col for col in columns}


       for index, col_id in enumerate(data.column_ids):
           column = col_map.get(col_id)
           if column:
               column.position = (index + 1) * POSITION_GAP
               session.add(column)


       await touch_project(session, column.project_id)
       await session.commit()


   @staticmethod
   async def create_task(
           session: AsyncSession,
           project_id: int,
           column_id: int,
           data: TaskCreate,
           author_id: int,
   ) -> Task:
       await BoardService._check_column_limit(session, column_id)


       if data.assignee_id is not None:
           stmt = (
               select(1)
               .where(
                   ProjectMember.project_id == project_id,
                   ProjectMember.user_id == data.assignee_id,
               )
               .limit(1)
           )
           if not (await session.scalar(stmt)):
               raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail="Assignee is not a member of this project.",
               )


       query = select(func.max(Task.position)).where(
           Task.column_id == column_id)
       max_pos = await session.scalar(query) or 0.0


       new_task = Task(
           title=data.title,
           description=data.description,
           priority=data.priority,
           project_id=project_id,
           column_id=column_id,
           assignee_id=data.assignee_id,
           author_id=author_id,
           position=max_pos + POSITION_GAP,
       )


       if data.tag_ids:
           tags_query = select(Tag).where(
               Tag.id.in_(data.tag_ids), Tag.project_id == project_id
           )
           tags = (await session.execute(tags_query)).scalars().all()
           if len(tags) != len(data.tag_ids):
               raise HTTPException(status_code=400, detail="Invalid tag IDs")
           new_task.tags = list(tags)


       session.add(new_task)
       await touch_project(session, project_id)
       await session.commit()


       return await BoardService._get_task_with_tags(session, new_task.id)


   @staticmethod
   async def get_project_tasks(
           session: AsyncSession,
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


       result = await session.execute(stmt)
       return result.scalars().all()


   @staticmethod
   async def move_task(
           session: AsyncSession,
           task: Task,
           data: TaskMove,
   ) -> Task:
       if task.column_id != data.new_column_id:
           col_check = await session.get(BoardColumn, data.new_column_id)
           if not col_check or col_check.project_id != task.project_id:
               raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail="Target column invalid or belongs to another project",
               )
           await BoardService._check_column_limit(session, data.new_column_id)


       attempts = 0
       while attempts < 2:
           attempts += 1
           new_position = await BoardService._calculate_new_position(
               session, data.new_column_id, data.after_task_id
           )


           if new_position is None:
               await BoardService._rebalance_column(session,
                                                    data.new_column_id)
               continue


           task.column_id = data.new_column_id
           task.position = new_position


           task.updated_at = datetime.now(timezone.utc)
           session.add(task)


           await touch_project(session, task.project_id)
           await session.commit()


           return task


       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail="Failed to move task due to position calculation error.",
       )


   @staticmethod
   async def _calculate_new_position(
           session: AsyncSession,
           column_id: int,
           after_task_id: int | None,
   ) -> float | None:
       if after_task_id is None:
           stmt = (
               select(Task.position)
               .where(Task.column_id == column_id)
               .order_by(Task.position.asc())
               .limit(1)
               .with_for_update()
           )
           first_pos = await session.scalar(stmt)


           if first_pos is None:
               return POSITION_GAP


           new_pos = first_pos / 2.0
           return new_pos if new_pos > MIN_POSITION_DELTA else None


       else:
           prev_task_stmt = (
               select(Task.position)
               .where(Task.id == after_task_id, Task.column_id == column_id)
               .with_for_update()
           )
           prev_pos = await session.scalar(prev_task_stmt)


           if prev_pos is None:
               raise HTTPException(
                   status_code=status.HTTP_409_CONFLICT,
                   detail="Anchor task not found in target column",
               )


           next_task_stmt = (
               select(Task.position)
               .where(Task.column_id == column_id, Task.position > prev_pos)
               .order_by(Task.position.asc())
               .limit(1)
               .with_for_update()
           )
           next_pos = await session.scalar(next_task_stmt)


           if next_pos is None:
               return prev_pos + POSITION_GAP


           delta = next_pos - prev_pos
           return (prev_pos + delta / 2.0) if delta > MIN_POSITION_DELTA else None


   @staticmethod
   async def _rebalance_column(session: AsyncSession, column_id: int):
       stmt = (
           select(Task)
           .where(Task.column_id == column_id)
           .order_by(Task.position.asc())
           .with_for_update()
       )
       tasks = (await session.execute(stmt)).scalars().all()


       for index, task in enumerate(tasks):
           task.position = (index + 1) * POSITION_GAP
           session.add(task)


       await session.flush()


   @staticmethod
   async def update_task(
           session: AsyncSession,
           task: Task,
           data: TaskUpdate,
   ) -> Task:
       if data.assignee_id is not None:
           if task.assignee_id != data.assignee_id:
               stmt = (
                   select(1)
                   .where(
                       ProjectMember.project_id == task.project_id,
                       ProjectMember.user_id == data.assignee_id,
                   )
                   .limit(1)
               )
               if not (await session.scalar(stmt)):
                   raise HTTPException(
                       status_code=status.HTTP_400_BAD_REQUEST,
                       detail="New assignee is not a member of this project.",
                   )


       if data.tag_ids is not None:
           tags_query = select(Tag).where(
               Tag.id.in_(data.tag_ids), Tag.project_id == task.project_id
           )
           tags = (await session.execute(tags_query)).scalars().all()
           if len(tags) != len(data.tag_ids):
               raise HTTPException(status_code=400, detail="Invalid tag IDs")
           task.tags = list(tags)


       update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
       for key, value in update_data.items():
           setattr(task, key, value)


       task.updated_at = datetime.now(timezone.utc)
       session.add(task)


       await touch_project(session, task.project_id)
       await session.commit()


       return await BoardService._get_task_with_tags(session, task.id)


   @staticmethod
   async def delete_task(
           session: AsyncSession,
           task: Task,
   ) -> None:
       await session.delete(task)
       await touch_project(session, task.project_id)
       await session.commit()


   @staticmethod
   async def _get_task_with_tags(session: AsyncSession, task_id: int) -> Task:
       stmt = select(Task).where(Task.id == task_id).options(
           selectinload(Task.tags))
       result = await session.execute(stmt)
       return result.scalar_one()
