# 02. Backend Deep Dive

## Purpose
Зафиксировать backend implementation-level context: bootstrapping, layers, auth/security, permissions, service responsibilities, transaction boundaries и error model, чтобы изменения были предсказуемыми и безопасными.

## Current Behavior
### 1) Runtime Bootstrap & Layering
Backend стартует через `FastAPI` app с lifecycle hook (`lifespan`) и централизованным подключением роутеров под `/api`.

Layer pattern:
- `router.py` — HTTP contract, dependencies wiring.
- `dependencies.py` — auth/permission checks.
- `service.py` — бизнес-логика и DB mutations.
- `models.py` + `schemas.py` — persistence and DTO layer.
- `errors.py` — unified error code catalog.

DB access идет через `DatabaseHelper` (`create_async_engine` + session maker), инжектируемый через `Depends`.

### 2) Auth Model (JWT + Cookie)
#### Token design
- Access token: JWT (`type=access`), подписан приватным RSA ключом.
- Refresh token: JWT (`type=refresh`) в `HttpOnly` cookie (`refresh_token`).

#### Endpoint behavior
- `POST /api/auth/login` → проверка username/email + password, выдача access + cookie refresh.
- `POST /api/auth/refresh` → читает cookie, валидирует refresh token type, выдает новый access + refresh cookie.
- `POST /api/auth/logout` → `delete_cookie(refresh_token)`.

### 3) Permission Model
#### Project-level checks
`projects/dependencies.py` разделяет:
- `ProjectAccessChecker` — возвращает `Project` объект (owner/manager/member).
- `ProjectPermissionChecker` — role-only gate.

#### Task-level checks
`boards/dependencies.py`:
- Owners/Managers bypass member constraints.
- Members могут изменять только свои assigned tasks (`check_assignee=True` на update/move path).

### 4) Effective Permissions Matrix (Observed)
| Domain Action | Backend Gate |
|---|---|
| Create/Update/Delete project | Owner |
| List project members | Member+ |
| Remove member | Manager+ (service-level extra restrictions) |
| Change member role | Owner |
| Create/Update/Delete column | Manager+ |
| Create task | Member+ |
| Update/Move task | Member own-task, Manager+, Owner |
| Delete task | Manager+ |
| Manage tags | Manager+ |
| Create/delete/list invitations | Manager+ |
| Accept invitation | Authenticated user |

### 5) Domain Services (Responsibility Map)
- `AuthService`: user auth, token issuance, logout.
- `UserService`: user CRUD-like profile ops, avatar upload/delete via S3.
- `ProjectService`: project lifecycle, member lifecycle, roles, default tag seeding.
- `BoardService`: columns/tasks CRUD, reorder/move algorithm, filters query.
- `TagService`: project tags CRUD with uniqueness checks.
- `InvitationService`: invite creation, listing, deletion, acceptance and membership creation.

### 6) Transaction Boundaries
Observed pattern mostly consistent:
- mutate entity/entities
- optional `touch_project`
- `commit` + error mapping to `ErrorCode.DATABASE_ERROR`

Notable exceptions:
- `ProjectService.update_member_role` calls `commit` and then `touch_project` without an extra commit.
- `InvitationService.delete_invitation` returns success even when invite id not found (idempotent behavior, but contract implicit).

### 7) Error Model & Response Normalization
- Backend defines explicit `ErrorCode` and `SuccessCode` enums.
- `HTTPException` details are normalized by custom exception handler to `{ "error": { "code": ... } }` shape.
- Unhandled exceptions become `UNKNOWN_ERROR` with status 500.

### 8) Logging
- Central setup at app startup.
- Console + rotating file (`logs/app.log`) handlers.
- Domain-level logger aliases (`auth_logger`, `board_logger`, etc.).

## Dependencies
- Crypto/auth: `pyjwt[crypto]`, RSA keypair files, `pwdlib[argon2]`.
- DB: `sqlalchemy[asyncio]`, `asyncpg`, `alembic`.
- Storage: `aioboto3` for avatars.
- API runtime: `fastapi[standard]`, `uvicorn`.

## Risks
- Role escalation risk in invitation flow: manager-level endpoint accepts arbitrary `ProjectRole`, including `OWNER`.
- Potential stale project recency (`updated_at`) in role update flow due commit ordering.
- Stateless refresh token model has no server-side revocation list/jti tracking.
- Email visibility policy for `UserPublic` may be broader than expected for collaboration-only usage.

## Open Questions
- Should managers be forbidden from issuing `OWNER` invitation roles?
- Is project `updated_at` intended to change after member role update? If yes, commit order should be fixed.
- Is current refresh-token model acceptable for production security policy, or rotation + revocation is required?
- Should `/api/users/{user_id}` expose email to any authenticated user?

## References
- `backend/light_task/src/main.py:30`
- `backend/light_task/src/main.py:55`
- `backend/light_task/src/db/database.py:13`
- `backend/light_task/src/db/database.py:22`
- `backend/light_task/src/db/database.py:38`
- `backend/light_task/src/auth/router.py:17`
- `backend/light_task/src/auth/router.py:33`
- `backend/light_task/src/auth/router.py:45`
- `backend/light_task/src/auth/service.py:20`
- `backend/light_task/src/auth/service.py:55`
- `backend/light_task/src/auth/service.py:72`
- `backend/light_task/src/security.py:12`
- `backend/light_task/src/security.py:60`
- `backend/light_task/src/security.py:72`
- `backend/light_task/src/auth/dependencies.py:14`
- `backend/light_task/src/auth/dependencies.py:30`
- `backend/light_task/src/auth/dependencies.py:72`
- `backend/light_task/src/projects/dependencies.py:16`
- `backend/light_task/src/projects/dependencies.py:53`
- `backend/light_task/src/projects/dependencies.py:83`
- `backend/light_task/src/projects/dependencies.py:91`
- `backend/light_task/src/boards/dependencies.py:40`
- `backend/light_task/src/boards/dependencies.py:91`
- `backend/light_task/src/boards/dependencies.py:105`
- `backend/light_task/src/projects/router.py:112`
- `backend/light_task/src/projects/service.py:270`
- `backend/light_task/src/projects/service.py:327`
- `backend/light_task/src/projects/service.py:328`
- `backend/light_task/src/invitations/router.py:26`
- `backend/light_task/src/invitations/schemas.py:13`
- `backend/light_task/src/invitations/service.py:35`
- `backend/light_task/src/invitations/service.py:78`
- `backend/light_task/src/invitations/service.py:88`
- `backend/light_task/src/users/router.py:50`
- `backend/light_task/src/users/schemas.py:36`
- `backend/light_task/src/users/schemas.py:41`
- `backend/light_task/src/errors.py:11`
- `backend/light_task/src/errors.py:61`
- `backend/light_task/src/errors.py:80`
- `backend/light_task/src/logger.py:38`
- `backend/light_task/src/logger.py:42`
- `backend/light_task/src/logger.py:70`
