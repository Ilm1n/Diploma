# 06. DevOps and Environments

## Purpose
Описать operational context проекта: dev/prod топологии, контейнеризацию, ingress/proxy behavior, CI/CD процесс и env contract, чтобы деплой и диагностика были воспроизводимыми.

## Current Behavior
### 1) Environment Topologies
#### Development (`docker-compose.dev.yml`)
- Services: `db` + `backend`.
- Backend запускается в reload-mode (`uvicorn ... --reload`).
- Source mounts for backend code and alembic migrations.
- DB healthcheck blocks backend startup via `depends_on` condition.

#### Production (`docker-compose.prod.yml`)
- Services: `gateway` (Caddy), `backend`, `db`.
- Gateway публикует `80/443` and `443/udp`.
- Backend and DB in separate internal networks with controlled linkage.
- Backend healthcheck uses `/api/health`.

### 2) Gateway (Caddy)
- Redirects alias domains to canonical `https://kantano.ru`.
- Adds security headers (HSTS, X-Frame-Options, etc.).
- Protects `/docs`, `/openapi.json`, `/redoc` with basic auth.
- Reverse proxies `/api/*` (and `/ws/*`) to backend.
- Serves SPA static files with `try_files {path} /index.html`.

### 3) Container Build and Startup
#### Backend image
- Multi-stage build with `uv` lock-based dependency sync.
- Runtime image: Python slim + non-root `appuser`.
- Entrypoint waits for DB and runs `alembic upgrade head` before app start.

#### Frontend image
- Multi-stage: Node build (`pnpm build`) then static serve from Caddy image.

### 4) CI/CD Pipeline (`.github/workflows/deploy.yml`)
Pipeline jobs:
1. `prepare` — compute short SHA tag.
2. `build-backend` — build/push backend image to GHCR.
3. `build-frontend` — build/push frontend image to GHCR.
4. `deploy` — create `.env` and certs, SCP files to VPS, SSH deploy via `docker compose pull/up --wait`.
5. `cleanup` — prune old package versions in registry.

Trigger mode currently: `workflow_dispatch` (manual), push trigger is commented out.

### 5) Environment Contract
Root `.env.template` defines backend-centric contract:
- DB credentials/host/port/echo.
- Run host/port/CORS origins.
- Invite base URL.
- Auth options (`AUTH_JWT__SECURE`, token TTL).
- S3 credentials + bucket.

Frontend has separate `.env.template` with `VITE_API_URL`, but current runtime code uses empty-string base URL expression.

### 6) Secrets and Boundaries
- JWT private/public keys expected in `certs/`.
- Production deploy workflow materializes `.env` and cert files from GitHub secrets.
- Swagger basic auth hash injected via `SWAGGER_HASH` env var.

## Dependencies
- Build/runtime: Docker, Docker Compose, GHCR.
- Ingress: Caddy 2.x.
- CI/CD: GitHub Actions + appleboy SCP/SSH actions.
- Database: PostgreSQL 15.
- TLS/certs for JWT signing keys managed outside git.

## Risks
- Manual-only deploy trigger can create drift between main branch and production if release discipline is weak.
- Caddy routes `/ws/*`, but no backend WebSocket handlers currently registered.
- `.gitignore` is minimal; runtime-generated files like `logs/` are not ignored by default.
- Frontend API URL env variable is currently not wired to API base URL logic.

## Open Questions
- Should push-to-main deploy be re-enabled with environment protection rules?
- Should `/ws/*` route remain reserved for roadmap or be removed until implemented?
- Should `.gitignore` include logs/build artifacts to reduce accidental commits?
- Should frontend env contract be normalized and validated in CI?

## References
- `docker-compose.dev.yml:3`
- `docker-compose.dev.yml:4`
- `docker-compose.dev.yml:15`
- `docker-compose.dev.yml:25`
- `docker-compose.dev.yml:36`
- `docker-compose.prod.yml:4`
- `docker-compose.prod.yml:18`
- `docker-compose.prod.yml:29`
- `docker-compose.prod.yml:56`
- `docker-compose.prod.yml:75`
- `docker-compose.prod.yml:71`
- `Caddyfile:9`
- `Caddyfile:17`
- `Caddyfile:21`
- `Caddyfile:23`
- `Caddyfile:39`
- `backend/light_task/Dockerfile:1`
- `backend/light_task/Dockerfile:11`
- `backend/light_task/Dockerfile:38`
- `backend/light_task/Dockerfile:40`
- `backend/light_task/entrypoint.sh:16`
- `frontend/light-task-frontend/Dockerfile:1`
- `frontend/light-task-frontend/Dockerfile:10`
- `frontend/light-task-frontend/Dockerfile:12`
- `.github/workflows/deploy.yml:1`
- `.github/workflows/deploy.yml:6`
- `.github/workflows/deploy.yml:27`
- `.github/workflows/deploy.yml:53`
- `.github/workflows/deploy.yml:80`
- `.github/workflows/deploy.yml:112`
- `.github/workflows/deploy.yml:121`
- `.github/workflows/deploy.yml:137`
- `.github/workflows/deploy.yml:139`
- `.github/workflows/deploy.yml:143`
- `.env.template:2`
- `.env.template:10`
- `.env.template:15`
- `.env.template:21`
- `.env.template:26`
- `frontend/light-task-frontend/.env.template:2`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`
- `.gitignore:1`
- `.gitignore:2`
