# 07. Risk Register

## Purpose
Зафиксировать приоритизированные findings аудита в формате, пригодном для backlog planning и безопасного исполнения изменений.

## Current Behavior
### Methodology
- Severity scale: `Critical`, `High`, `Medium`, `Low`.
- Priority scale: `P0` (now), `P1` (next), `P2` (planned), `P3` (later).
- Evidence uses concrete `path:line` references from repository.

### Findings
| ID | Severity | Impact | Reproduction / Conditions | Evidence (`path:line`) | Recommendation | Priority | Status |
|---|---|---|---|---|---|---|---|
| R-001 | Critical | Privilege escalation: manager can indirectly grant owner access via invite role. | Was reproducible when user with `MANAGER` role called invite creation with `role=OWNER`. Service now validates inviter membership and blocks non-owner escalation. | `backend/light_task/src/invitations/service.py:32`; `backend/light_task/src/invitations/service.py:56`; `frontend/light-task-frontend/src/modules/invitations/components/InviteMemberDialog.vue:31` | Keep service-layer role ceiling validation as source of truth; frontend may hide invalid options for UX only. | P0 | Resolved |
| R-002 | High | Project recency may stay stale after member role change (sorting/UX inconsistency). | Was reproducible because method committed before `touch_project`. Current flow touches project before commit, so `updated_at` is persisted in the same transaction. | `backend/light_task/src/projects/service.py:327`; `backend/light_task/src/projects/service.py:328`; `backend/light_task/src/common/touch.py:9` | Keep `touch_project` before final commit in mutating membership flows. | P1 | Resolved |
| R-003 | Medium | Environment contract mismatch for frontend API URL; deploy portability risk outside same-origin proxy model. | Was reproducible when runtime base URL ignored `VITE_API_URL`. Current frontend reads env value, trims trailing slashes, and falls back to same-origin proxy mode when empty. | `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`; `frontend/light-task-frontend/src/api/config/axios-instance.ts:6`; `frontend/light-task-frontend/.env.template:3` | Keep env-based base URL wiring and document empty-string same-origin fallback. | P1 | Resolved |
| R-004 | Medium | Potential privacy overexposure: authenticated users can fetch other users with email included. | Was reproducible because `/api/users/{user_id}` returned `UserPublic` with `email`. Current schema split keeps `UserPublic` without email and uses `UserCollaborator` only in project member payloads. | `backend/light_task/src/users/router.py:50`; `backend/light_task/src/users/schemas.py:36`; `backend/light_task/src/users/schemas.py:43`; `backend/light_task/src/projects/schemas.py:55` | Preserve separate public/collaborator DTOs; add any future email exposure only behind explicit contract boundaries. | P1 | Resolved |
| R-005 | Medium | Security posture gap: refresh tokens are stateless and not revocable server-side. | Stolen valid refresh token remains usable until expiration. | `backend/light_task/src/security.py:72`; `backend/light_task/src/auth/service.py:55`; `backend/light_task/src/auth/dependencies.py:72` | Introduce token rotation and server-side revocation/JTI tracking. | P2 | Open |
| R-006 | Medium | Testing safety net is weak; validation described mostly as manual Schemathesis runs. | No committed automated test suite in current tree; README only lists manual commands. | `backend/light_task/README.md:14`; `backend/light_task/README.md:16`; `backend/light_task/README.md:19` | Add CI test stages (backend unit/integration + frontend tests + smoke). | P1 | Open |
| R-007 | Low | Product messaging mismatch: landing claims WebSockets realtime without backend WebSocket handlers. | Compare landing statement with backend registered routes. | `frontend/light-task-frontend/src/modules/landing/pages/LandingPage.vue:82`; `backend/light_task/src/main.py:55`; `backend/light_task/src/main.py:60` | Align copy with current capability or implement realtime transport. | P3 | Open |
| R-008 | Low | Infrastructure mismatch: gateway reserves `/ws/*` route but backend does not expose WS endpoints. | WebSocket path routed by Caddy, but no ws handlers in app. | `Caddyfile:21`; `backend/light_task/src/main.py:55` | Remove unused route or keep as documented roadmap endpoint placeholder. | P3 | Open |
| R-009 | Medium | Repository hygiene risk: runtime outputs and local artifacts can be committed accidentally. | Was reproducible with minimal root ignore rules while app writes `logs/app.log`. Root `.gitignore` now excludes env files, virtualenvs, node artifacts, logs, coverage and local postgres directories. | `.gitignore:1`; `.gitignore:6`; `.gitignore:23`; `backend/light_task/src/logger.py:42`; `backend/light_task/src/logger.py:70` | Keep root ignore rules aligned with runtime outputs and local tooling artifacts. | P2 | Resolved |
| R-010 | Low | Invitation delete endpoint is silently idempotent for missing ID (no explicit not-found signal). | Was reproducible because delete path returned success when invite was absent. Current contract returns `404` with `INVITATION_NOT_FOUND` and documents it in router/OpenAPI. | `backend/light_task/src/invitations/router.py:49`; `backend/light_task/src/invitations/service.py:103`; `backend/light_task/src/invitations/service.py:116` | Keep explicit not-found behavior in backend contract and generated client. | P3 | Resolved |
| R-011 | Low | Migration readability overhead: two early “init” revisions can confuse newcomers. | Revision chain starts with two init-like migrations. | `backend/light_task/alembic/versions/2025_12_15_0227-25c007f9fa47_init_migration.py:16`; `backend/light_task/alembic/versions/2025_12_15_2006-027a79ca5e8c_init_migration.py:16` | Add migration history note (done in docs) and naming guideline for new revisions. | P3 | Open |
| R-012 | Low | Deploy process is manual-trigger only, increasing risk of production drift from main branch state. | Workflow trigger is `workflow_dispatch`; push trigger commented. | `.github/workflows/deploy.yml:6`; `.github/workflows/deploy.yml:80` | Add protected auto-deploy or release-based pipeline with approvals. | P2 | Open |

## Dependencies
- Depends on current router/service/config behavior in backend and frontend.
- Depends on current infrastructure definitions (`docker-compose`, `Caddyfile`, GitHub Actions workflow).

## Risks
- This register can become stale after fixes unless maintained alongside code changes.
- Some findings are policy-dependent (security/privacy/product), require owner decision before implementation.

## Open Questions
- Какая целевая security model для refresh-token lifecycle (rotation, revocation, session limits)?
- Нужна ли privacy boundary между collaborator lookup и public profile lookup?
- Какой rollout policy для risky permission changes (feature flag, staged release, audit logs)?

## References
- `backend/light_task/src/invitations/service.py:32`
- `backend/light_task/src/invitations/service.py:56`
- `frontend/light-task-frontend/src/modules/invitations/components/InviteMemberDialog.vue:31`
- `backend/light_task/src/projects/service.py:327`
- `backend/light_task/src/projects/service.py:328`
- `backend/light_task/src/common/touch.py:9`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:6`
- `frontend/light-task-frontend/.env.template:3`
- `backend/light_task/src/users/router.py:50`
- `backend/light_task/src/users/schemas.py:36`
- `backend/light_task/src/users/schemas.py:43`
- `backend/light_task/src/projects/schemas.py:55`
- `backend/light_task/src/security.py:72`
- `backend/light_task/src/auth/service.py:55`
- `backend/light_task/src/auth/dependencies.py:72`
- `backend/light_task/README.md:14`
- `backend/light_task/README.md:16`
- `backend/light_task/README.md:19`
- `frontend/light-task-frontend/src/modules/landing/pages/LandingPage.vue:82`
- `backend/light_task/src/main.py:55`
- `backend/light_task/src/main.py:60`
- `Caddyfile:21`
- `.gitignore:1`
- `.gitignore:6`
- `.gitignore:23`
- `backend/light_task/src/logger.py:42`
- `backend/light_task/src/logger.py:70`
- `backend/light_task/src/invitations/router.py:49`
- `backend/light_task/src/invitations/service.py:103`
- `backend/light_task/src/invitations/service.py:116`
- `backend/light_task/alembic/versions/2025_12_15_0227-25c007f9fa47_init_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_15_2006-027a79ca5e8c_init_migration.py:16`
- `.github/workflows/deploy.yml:6`
- `.github/workflows/deploy.yml:80`
