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
| R-001 | Critical | Privilege escalation: manager can indirectly grant owner access via invite role. | User with `MANAGER` role calls invite creation with `role=OWNER`. | `backend/light_task/src/invitations/router.py:26`; `backend/light_task/src/invitations/schemas.py:13`; `backend/light_task/src/invitations/service.py:35` | Enforce max assignable role by caller (manager <= manager), validate in service layer. | P0 | Open |
| R-002 | High | Project recency may stay stale after member role change (sorting/UX inconsistency). | Call member role update; method commits before `touch_project`, with no second commit. | `backend/light_task/src/projects/service.py:327`; `backend/light_task/src/projects/service.py:328`; `backend/light_task/src/common/touch.py:9` | Move `touch_project` before commit or add explicit commit after touch. Add regression test. | P1 | Open |
| R-003 | Medium | Environment contract mismatch for frontend API URL; deploy portability risk outside same-origin proxy model. | Set `VITE_API_URL`, observe current code still uses empty base URL expression. | `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`; `frontend/light-task-frontend/.env.template:2` | Wire base URL to env with explicit fallback and docs/validation. | P1 | Open |
| R-004 | Medium | Potential privacy overexposure: authenticated users can fetch other users with email included. | Any authenticated user requests `/api/users/{user_id}`. | `backend/light_task/src/users/router.py:50`; `backend/light_task/src/users/schemas.py:41` | Split public/internal schemas; hide email unless explicit permission. | P1 | Open |
| R-005 | Medium | Security posture gap: refresh tokens are stateless and not revocable server-side. | Stolen valid refresh token remains usable until expiration. | `backend/light_task/src/security.py:72`; `backend/light_task/src/auth/service.py:55`; `backend/light_task/src/auth/dependencies.py:72` | Introduce token rotation and server-side revocation/JTI tracking. | P2 | Open |
| R-006 | Medium | Testing safety net is weak; validation described mostly as manual Schemathesis runs. | No committed automated test suite in current tree; README only lists manual commands. | `backend/light_task/README.md:14`; `backend/light_task/README.md:16`; `backend/light_task/README.md:19` | Add CI test stages (backend unit/integration + frontend tests + smoke). | P1 | Open |
| R-007 | Low | Product messaging mismatch: landing claims WebSockets realtime without backend WebSocket handlers. | Compare landing statement with backend registered routes. | `frontend/light-task-frontend/src/modules/landing/pages/LandingPage.vue:82`; `backend/light_task/src/main.py:55`; `backend/light_task/src/main.py:60` | Align copy with current capability or implement realtime transport. | P3 | Open |
| R-008 | Low | Infrastructure mismatch: gateway reserves `/ws/*` route but backend does not expose WS endpoints. | WebSocket path routed by Caddy, but no ws handlers in app. | `Caddyfile:21`; `backend/light_task/src/main.py:55` | Remove unused route or keep as documented roadmap endpoint placeholder. | P3 | Open |
| R-009 | Medium | Repository hygiene risk: `.gitignore` minimal while app writes `logs/`. | Running app creates `logs/app.log`; path currently not ignored by default. | `.gitignore:1`; `.gitignore:2`; `backend/light_task/src/logger.py:42`; `backend/light_task/src/logger.py:70` | Expand `.gitignore` for logs/artifacts/secrets-related outputs. | P2 | Open |
| R-010 | Low | Invitation delete endpoint is silently idempotent for missing ID (no explicit not-found signal). | Delete non-existing invitation returns success path (no else branch). | `backend/light_task/src/invitations/service.py:78`; `backend/light_task/src/invitations/service.py:88` | Decide explicit contract: keep idempotent and document, or return 404 for visibility. | P3 | Open |
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
- `backend/light_task/src/invitations/router.py:26`
- `backend/light_task/src/invitations/schemas.py:13`
- `backend/light_task/src/invitations/service.py:35`
- `backend/light_task/src/projects/service.py:327`
- `backend/light_task/src/projects/service.py:328`
- `backend/light_task/src/common/touch.py:9`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`
- `frontend/light-task-frontend/.env.template:2`
- `backend/light_task/src/users/router.py:50`
- `backend/light_task/src/users/schemas.py:41`
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
- `.gitignore:2`
- `backend/light_task/src/logger.py:42`
- `backend/light_task/src/logger.py:70`
- `backend/light_task/src/invitations/service.py:78`
- `backend/light_task/src/invitations/service.py:88`
- `backend/light_task/alembic/versions/2025_12_15_0227-25c007f9fa47_init_migration.py:16`
- `backend/light_task/alembic/versions/2025_12_15_2006-027a79ca5e8c_init_migration.py:16`
- `.github/workflows/deploy.yml:6`
- `.github/workflows/deploy.yml:80`
