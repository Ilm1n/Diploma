# 08. Onboarding and Agent Playbook

## Purpose
Дать пошаговый практический guide для нового инженера/агента: как войти в контекст за `30/60` минут, как выполнять диагностику и как менять код безопасно с учетом известных рисков.

## Current Behavior
### 1) 30-Minute Onboarding
#### Step 1: Read context docs
Read in order:
1. `01-system-overview.md`
2. `07-risk-register.md`
3. One deep-dive by task type (`02` backend / `03` frontend / `06` DevOps)

#### Step 2: Confirm project shape
- Verify monorepo structure:
  - `backend/light_task`
  - `frontend/light-task-frontend`
  - `docker-compose.dev.yml`
  - `docker-compose.prod.yml`

#### Step 3: Understand contract boundaries
- API is under `/api`.
- Roles are `OWNER`, `MANAGER`, `MEMBER`.
- Session model: access token in memory + refresh token in cookie.

### 2) 60-Minute Hands-On Setup
### Backend local run (containerized)
```bash
cp .env.template .env
# generate JWT keys in backend/light_task/certs or ./certs depending on run mode
docker compose -f docker-compose.dev.yml up --build
```

### Frontend local run (optional separate process)
```bash
cd frontend/light-task-frontend
pnpm install
pnpm dev
```

### Quick runtime checks
```bash
curl -f http://127.0.0.1:8000/api/health
```
- Open app and validate:
  - register/login flow
  - project creation
  - board load
  - task move
  - invitation accept flow

### 3) Diagnostic Command Set
### Repo orientation
```bash
rg --files
rg -n "@router\.(get|post|patch|delete)" backend/light_task/src -g '*router.py'
rg -n "defineStore\(" frontend/light-task-frontend/src
```

### Contract checks
```bash
rg -n '^\s+"/.*": \{' frontend/light-task-frontend/openapi.json
```

### Risk-focused checks
```bash
# invite role behavior
rg -n "check_project_manager|role: ProjectRole" backend/light_task/src/invitations/*.py

# project touch ordering
rg -n "update_member_role|touch_project|commit" backend/light_task/src/projects/service.py

# frontend API base URL wiring
rg -n "API_BASE_URL|VITE_API_URL" frontend/light-task-frontend/src/api/config/axios-instance.ts frontend/light-task-frontend/.env.template
```

### 4) Safe Change Rules (Agent-Oriented)
- Always read `07-risk-register.md` before changing auth/permissions/invitations.
- For API behavior changes:
  1. Update backend router/service/schema.
  2. Regenerate frontend API client (`pnpm gen:api`) if openapi changed.
  3. Update `04-api-contract.md` and risk register status.
- For DB changes:
  1. Create Alembic migration.
  2. Validate upgrade path.
  3. Update `05-data-model-and-migrations.md`.
- For deployment/config changes:
  1. Sync compose/Caddy/workflow changes.
  2. Update `06-devops-and-environments.md`.

### 5) Change Checklist Before Merge
- Does this change affect roles/permissions?
- Does this change affect token/session flow?
- Does this change affect API contract or DTO shape?
- Does this change affect migration history or indexes?
- Did you update corresponding docs and risk status?

### 6) Suggested First Tasks For New Contributors
- `Task A`: fix frontend API base URL env wiring.
- `Task B`: prohibit manager-created owner invitations.
- `Task C`: fix `touch_project` commit ordering in member role update.
- `Task D`: expand `.gitignore` for runtime outputs.

## Dependencies
- Requires Docker/Compose for quick backend start.
- Requires Node + pnpm for frontend local workflow.
- Requires valid `.env` and JWT key pair.

## Risks
- New contributors may accidentally change behavior without considering permission matrix.
- Contract drift can happen if backend API changed but frontend client/docs not synchronized.
- Migration changes without documentation update reduce recoverability for future agents.

## Open Questions
- Should onboarding include mandatory smoke-test script in CI?
- Should repo include a single `make`/`task` entrypoint for setup and checks?
- What minimum evidence is required in PR description for auth/permission changes?

## References
- `docs/project-audit/01-system-overview.md`
- `docs/project-audit/02-backend-deep-dive.md`
- `docs/project-audit/03-frontend-deep-dive.md`
- `docs/project-audit/04-api-contract.md`
- `docs/project-audit/05-data-model-and-migrations.md`
- `docs/project-audit/06-devops-and-environments.md`
- `docs/project-audit/07-risk-register.md`
- `docker-compose.dev.yml:3`
- `backend/light_task/src/main.py:55`
- `backend/light_task/src/projects/constants.py:4`
- `backend/light_task/src/auth/service.py:55`
- `backend/light_task/src/auth/dependencies.py:72`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`
- `frontend/light-task-frontend/.env.template:2`
