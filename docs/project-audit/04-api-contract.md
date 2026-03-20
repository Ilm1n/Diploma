# 04. API Contract

## Purpose
Задокументировать HTTP contract backend (`/api/*`) в формате, удобном для интеграции и проверок регрессий: endpoint catalog, auth requirements, shape conventions и caveats.

## Current Behavior
### 1) Contract Conventions
- Base path: `/api`.
- Health check: `/api/health`.
- DTO serialization: `camelCase` aliasing from backend schemas.
- Errors normalized to `{ error: { code, params? } }` for known domain errors.

### 2) Endpoint Catalog (Grouped)
### Auth
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/auth/login` | Public | OAuth2 password form, returns access token + sets refresh cookie |
| POST | `/api/auth/refresh` | Refresh cookie | Returns new access token + refresh cookie |
| POST | `/api/auth/logout` | Optional auth context | Deletes refresh cookie |

### Users
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/users/register` | Public | Creates user |
| GET | `/api/users/me` | Bearer | Current user profile |
| PATCH | `/api/users/me` | Bearer | Update username/full_name |
| GET | `/api/users/{user_id}` | Bearer | Public-ish user data includes email |
| POST | `/api/users/me/avatar` | Bearer | Multipart avatar upload |
| DELETE | `/api/users/me/avatar` | Bearer | Removes avatar |

### Projects & Members
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/projects/` | Bearer | Create project |
| GET | `/api/projects/` | Bearer | List current user projects |
| GET | `/api/projects/{project_id}` | Bearer + membership | Project details |
| PATCH | `/api/projects/{project_id}` | Owner | Update project |
| DELETE | `/api/projects/{project_id}` | Owner | Delete project |
| GET | `/api/projects/{project_id}/members` | Member+ | List members |
| DELETE | `/api/projects/{project_id}/members/{user_id}` | Manager+ | Remove member (extra service checks) |
| PATCH | `/api/projects/{project_id}/members/{user_id}` | Owner | Change member role |

### Board / Tasks
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/projects/{project_id}/columns` | Member+ | Board columns with tasks |
| POST | `/api/projects/{project_id}/columns` | Manager+ | Create column |
| PATCH | `/api/projects/{project_id}/columns/{column_id}` | Manager+ | Update column |
| DELETE | `/api/projects/{project_id}/columns/{column_id}` | Manager+ | Delete column |
| POST | `/api/projects/{project_id}/columns/reorder` | Manager+ | Reorder columns |
| POST | `/api/projects/{project_id}/columns/{column_id}/tasks` | Member+ | Create task |
| GET | `/api/projects/{project_id}/tasks` | Member+ | Task list with optional filters |
| GET | `/api/tasks/{task_id}` | Member+ | Task details |
| PATCH | `/api/tasks/{task_id}/move` | Member own-task or Manager+ | Move task |
| PATCH | `/api/tasks/{task_id}` | Member own-task or Manager+ | Update task |
| DELETE | `/api/tasks/{task_id}` | Manager+ | Delete task |

### Tags
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/projects/{project_id}/tags` | Member+ | List tags |
| POST | `/api/projects/{project_id}/tags` | Manager+ | Create tag |
| PATCH | `/api/tags/{tag_id}` | Manager+ | Update tag |
| DELETE | `/api/tags/{tag_id}` | Manager+ | Delete tag |

### Invitations
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/projects/{project_id}/invite` | Manager+ | Create invite link |
| GET | `/api/projects/{project_id}/invitations` | Manager+ | List project invites |
| DELETE | `/api/projects/{project_id}/invitations/{invitation_id}` | Manager+ | Delete invite |
| POST | `/api/invitations/{token}/accept` | Bearer | Accept invite |

### System
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/health` | Public | Liveness endpoint |

### 3) Important Request/Response Shapes
- Task create/update supports tag assignment by `tag_ids`.
- Task move contract: `{ newColumnId, afterTaskId|null }`.
- Project/member role enum: `OWNER | MANAGER | MEMBER`.
- Invitation create supports role/email/max_uses/expires_in_days.
- Invitation read includes computed `link` using configured `invite.base_url`.

### 4) Error/Success Semantics
- Domain errors map to `ErrorCode` values (frontend maps these codes to RU messages).
- Invitation accept uses success payload with codes like `INVITATION_ACCEPT_SUCCESS` and `ALREADY_PROJECT_MEMBER`.

## Dependencies
- Contract source of truth: backend routers + schemas + `openapi.json` snapshot in frontend.
- Client source of truth for frontend consumption: generated services in `src/api/client/services/*.ts`.

## Risks
- Contract drift risk: `openapi.json` and generated frontend client are snapshot-based and can become stale if backend changes without regeneration.
- Authorization caveat: invitation role creation currently permits elevated role values when caller is manager.
- Privacy caveat: `UserPublic` includes email and is returned by `/users/{user_id}`.

## Open Questions
- Should `/users/{user_id}` return a reduced public schema without email?
- Should invitation creation enforce caller maximum role (e.g., manager cannot invite owner)?
- Should CI include OpenAPI diff check to prevent contract drift?

## References
- `backend/light_task/src/schemas.py:10`
- `backend/light_task/src/errors.py:80`
- `backend/light_task/src/auth/router.py:17`
- `backend/light_task/src/auth/router.py:33`
- `backend/light_task/src/auth/router.py:45`
- `backend/light_task/src/users/router.py:20`
- `backend/light_task/src/users/router.py:32`
- `backend/light_task/src/users/router.py:40`
- `backend/light_task/src/users/router.py:50`
- `backend/light_task/src/users/router.py:59`
- `backend/light_task/src/users/router.py:81`
- `backend/light_task/src/projects/router.py:26`
- `backend/light_task/src/projects/router.py:41`
- `backend/light_task/src/projects/router.py:49`
- `backend/light_task/src/projects/router.py:60`
- `backend/light_task/src/projects/router.py:73`
- `backend/light_task/src/projects/router.py:82`
- `backend/light_task/src/projects/router.py:91`
- `backend/light_task/src/projects/router.py:106`
- `backend/light_task/src/boards/router.py:31`
- `backend/light_task/src/boards/router.py:40`
- `backend/light_task/src/boards/router.py:54`
- `backend/light_task/src/boards/router.py:67`
- `backend/light_task/src/boards/router.py:79`
- `backend/light_task/src/boards/router.py:92`
- `backend/light_task/src/boards/router.py:113`
- `backend/light_task/src/boards/router.py:127`
- `backend/light_task/src/boards/router.py:134`
- `backend/light_task/src/boards/router.py:143`
- `backend/light_task/src/boards/router.py:152`
- `backend/light_task/src/tags/router.py:14`
- `backend/light_task/src/tags/router.py:23`
- `backend/light_task/src/tags/router.py:37`
- `backend/light_task/src/tags/router.py:46`
- `backend/light_task/src/invitations/router.py:18`
- `backend/light_task/src/invitations/router.py:37`
- `backend/light_task/src/invitations/router.py:46`
- `backend/light_task/src/invitations/router.py:59`
- `backend/light_task/src/main.py:81`
- `backend/light_task/src/boards/schemas.py:30`
- `backend/light_task/src/boards/schemas.py:47`
- `backend/light_task/src/projects/constants.py:4`
- `backend/light_task/src/invitations/schemas.py:13`
- `backend/light_task/src/invitations/schemas.py:32`
- `frontend/light-task-frontend/openapi.json:8`
- `frontend/light-task-frontend/openapi.json:1765`
- `frontend/light-task-frontend/src/api/client/services/DefaultService.ts:1`
