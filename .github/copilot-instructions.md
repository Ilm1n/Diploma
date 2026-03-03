Project snapshot — quick guide for AI coding agents

Purpose: brief, actionable notes to get productive in this repo (backend + frontend).

- **Big picture:**
  - **Services:** backend is a FastAPI app at [backend/light_task/src](backend/light_task/src) and frontend is a Vue 3 + Vite app at [frontend/light-task-frontend](frontend/light-task-frontend).
  - **API surface:** backend mounts all routers under `/api` (see [backend/light_task/src/main.py](backend/light_task/src/main.py#L1-L60)).
  - **Data flow:** frontend consumes REST endpoints (OpenAPI published by backend); the frontend includes a checked-in `openapi.json` and a client generator (`gen:api`).

- **Where to start reading (high value files):**
  - App entry: [backend/light_task/src/main.py](backend/light_task/src/main.py#L1-L80)
  - Settings: [backend/light_task/src/config.py](backend/light_task/src/config.py#L1-L80)
  - DB helper: [backend/light_task/src/db/database.py](backend/light_task/src/db/database.py#L1-L120)
  - Example router pattern: [backend/light_task/src/projects/router.py](backend/light_task/src/projects/router.py#L1-L40)
  - Frontend entry: [frontend/light-task-frontend/src/main.ts](frontend/light-task-frontend/src/main.ts#L1-L80)
  - Frontend scripts + client gen: [frontend/light-task-frontend/package.json](frontend/light-task-frontend/package.json#L1-L40)

- **Architectural patterns & conventions (explicit):**
  - Router → Service → Models/Schemas: each feature folder uses `router.py`, `service.py`, `models.py`, `schemas.py`, `dependencies.py`. Add new endpoints following this layout. See `projects/` as an example.
  - Async DB usage: uses SQLAlchemy asyncio and an app-wide `db_helper` with `get_async_session()` (see `db/database.py`). Use `async with` sessions and `expire_on_commit=False` pattern.
  - Settings injection: uses `pydantic-settings` with env prefix `LIGHTTASK_CONFIG__` and nested delimiter `__` — override configs via env vars or the repo `.env` referenced in `config.py`.
  - JWT & secrets: RSA keys expected in `src/certs` (paths configured in `config.py`); S3 settings present in config for file storage.
  - Responses use ORJSON by default (`default_response_class=ORJSONResponse` in `main.py`).

- **Common developer workflows & commands**
  - Backend (dev): from repo root:
    ```bash
    cd backend/light_task/src
    # ensure env vars (or .env) are available
    python -m uvicorn main:main_app --reload --host 127.0.0.1 --port 8000
    ```
  - DB migrations (alembic): use the `alembic.ini` in `backend/light_task` and the `alembic/` folder:
    ```bash
    cd backend/light_task
    alembic -c alembic.ini revision --autogenerate -m "your message"
    alembic -c alembic.ini upgrade head
    ```
  - Frontend (dev & build):
    ```bash
    cd frontend/light-task-frontend
    pnpm install
    pnpm dev
    pnpm build
    ```
  - Regenerate TypeScript API client when OpenAPI changes:
    ```bash
    cd frontend/light-task-frontend
    pnpm run gen:api
    ```
  - Docker / production: `docker-compose.prod.yml` and service Dockerfiles are at project root — prefer `docker-compose -f docker-compose.prod.yml up --build` for prod container runs.

- **Integration and external deps to watch for:**
  - Postgres (asyncpg) — DB URL built in config as `postgresql+asyncpg`.
  - S3-compatible storage (configured by `S3Config` in `config.py`).
  - OpenAPI client generation: `openapi-typescript-codegen` configured in frontend `package.json`.

- **Small actionable rules for PRs & edits (project-specific):**
  - Follow the feature folder layout (router/service/models/schemas). Add DB models and then a migration in `alembic/versions`.
  - Use typed Pydantic schemas for request/response models; routers commonly use `response_model=` on endpoints.
  - Use dependency providers (`get_*_service`) and FastAPI `Depends` for services and auth checks (see `projects/router.py`).

If anything here is unclear or you'd like more examples (e.g., a new endpoint scaffold), tell me which area and I will expand or adjust the file.
