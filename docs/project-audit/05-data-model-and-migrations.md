# 05. Data Model and Migrations

## Purpose
Собрать database-level context: сущности, связи, constraints/indexes, эволюция схемы через Alembic и жизненные циклы данных, чтобы безопасно планировать DB-изменения.

## Current Behavior
### 1) Core Entities and Relationships
#### `users`
- Identity: `id`, `email`, `username`, `hashed_password`.
- Profile: `full_name`, `avatar_url`, `is_active`, `is_admin`.
- Relation: one-to-many with `project_members`.

#### `projects`
- `owner_id -> users.id` (`CASCADE`).
- Has many `project_members`, `board_columns`, `tags`.
- Includes visual field `color`.

#### `project_members`
- Join entity (`project_id`, `user_id`, `role`, `joined_at`).
- Enforces uniqueness per `(project_id, user_id)`.

#### `board_columns`
- Belongs to project.
- Ordered by `position` (float gap strategy).
- Optional `tasks_limit`.

#### `tasks`
- Belongs to project and column.
- Optional `assignee_id` and `author_id` to users (`SET NULL`).
- Ordered by `position`.
- Many-to-many with tags via `task_tags`.

#### `tags` and `task_tags`
- Tag unique per `(project_id, name)`.
- `task_tags` pivot with composite PK and additional index by `(tag_id, task_id)`.

#### `project_invitations`
- Tokenized invitations bound to project.
- Supports role, optional email targeting, expiry and usage limits.

### 2) Constraint & Index Strategy
Examples of important protections:
- Name/title non-empty checks for projects/columns/tasks.
- Unique constraints for project membership and tag names per project.
- Access/perf indexes:
  - `tasks(column_id, position)` for board ordering.
  - `tasks(project_id, updated_at)` for recency listings.
  - `project_members(project_id, joined_at)` for membership ordering.
  - `project_invitations(project_id, created_at)` for invite listing.

### 3) Migration Timeline (Alembic)
Linear revision chain:
1. `25c007f9fa47` — initial schema.
2. `027a79ca5e8c` — enum/constraint adjustments.
3. `288e2d4cb6fb` — tags + task_tags.
4. `2041e17e1d0d` — project invitations (initial).
5. `40efe5e0c1b7` — invitation usage model (`max_uses`, `used_count`).
6. `e385a69fcf23` — `tasks_limit` on columns.
7. `4b1f02efc194` — color fields + several indexes.
8. `0c8ec9b25887` — additional indexes for hot paths.

### 4) Data Lifecycle Highlights
- Project creation auto-seeds default tags.
- Multiple mutation flows call `touch_project()` to keep project recency (`updated_at`) fresh.
- Invitation accept flow increments usage counters and creates membership atomically in one service method.

### 5) Migration/Schema Operational Notes
- Alembic uses project metadata from SQLAlchemy models and async migration engine.
- Runtime container entrypoint executes `alembic upgrade head` before starting app.

## Dependencies
- PostgreSQL 15 as primary datastore.
- SQLAlchemy metadata naming convention from settings.
- Alembic revision scripts as canonical schema history.

## Risks
- Business logic depends on `position` float arithmetic for ordering; high-frequency drag/drop can produce rebalance pressure.
- Some recency updates rely on service call ordering (see risk register for specific case).
- Migration history starts with two “init” revisions, which increases cognitive load for new maintainers.

## Open Questions
- Нужно ли перейти на integer-based ordering strategy для задач/колонок при росте нагрузки?
- Требуется ли additional composite index для частых task filter combinations (`assignee`, `priority`, `tag`)?
- Нужно ли формализовать policy по migration naming/description для будущих изменений?

## References
- `backend/light_task/src/users/models.py:13`
- `backend/light_task/src/projects/models.py:27`
- `backend/light_task/src/projects/models.py:61`
- `backend/light_task/src/boards/models.py:25`
- `backend/light_task/src/boards/models.py:49`
- `backend/light_task/src/tags/models.py:21`
- `backend/light_task/src/tags/models.py:35`
- `backend/light_task/src/invitations/models.py:15`
- `backend/light_task/src/projects/models.py:30`
- `backend/light_task/src/projects/models.py:64`
- `backend/light_task/src/projects/models.py:65`
- `backend/light_task/src/projects/models.py:66`
- `backend/light_task/src/boards/models.py:28`
- `backend/light_task/src/boards/models.py:29`
- `backend/light_task/src/boards/models.py:52`
- `backend/light_task/src/boards/models.py:53`
- `backend/light_task/src/boards/models.py:54`
- `backend/light_task/src/boards/models.py:55`
- `backend/light_task/src/boards/models.py:56`
- `backend/light_task/src/tags/models.py:32`
- `backend/light_task/src/tags/models.py:38`
- `backend/light_task/src/invitations/models.py:18`
- `backend/light_task/alembic/versions/2025_12_15_0227-25c007f9fa47_init_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_15_2006-027a79ca5e8c_init_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_16_0239-288e2d4cb6fb_tags_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_16_0354-2041e17e1d0d_invites_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_16_0441-40efe5e0c1b7_update_invite_model_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_16_0508-e385a69fcf23_add_tasks_limit_to_columns.py:16`
- `backend/light_task/alembic/versions/2025_12_22_0040-4b1f02efc194_add_color_to_projects_and_tags.py:16`
- `backend/light_task/alembic/versions/2026_03_08_0216-0c8ec9b25887_add_new_indexes.py:16`
- `backend/light_task/src/projects/service.py:30`
- `backend/light_task/src/common/touch.py:9`
- `backend/light_task/src/projects/service.py:256`
- `backend/light_task/src/boards/service.py:66`
- `backend/light_task/src/invitations/service.py:103`
- `backend/light_task/alembic/env.py:23`
- `backend/light_task/alembic/env.py:55`
- `backend/light_task/entrypoint.sh:16`
