# 03. Frontend Deep Dive

## Purpose
Описать фактическую frontend-архитектуру (Vue/Pinia/API integration), чтобы быстро ориентироваться в state/data flows, auth lifecycle, UI-модулях и внешних интеграциях.

## Current Behavior
### 1) App Bootstrap
Application стартует в `main.ts`:
- `createPinia()` + router + head manager.
- PrimeVue theme preset.
- Analytics bootstrap (`bootstrapAnalytics(router)`).

`App.vue` перед рендером основного `router-view` делает `authStore.restoreSession()` и показывает loading overlay до готовности.

### 2) Routing & Guards
Router structure:
- Public: landing, login, register, invite accept, not-found.
- Auth-only under `AppLayout`: projects, board, profile.

Guard behavior (`beforeEach`):
- Для login/register пытается восстановить сессию и редиректит в `/projects`, если уже аутентифицирован.
- Для `requiresAuth` роутов вызывает `restoreSession`; при провале редиректит в `/login`.

### 3) State Architecture (Pinia)
#### `auth.store`
- Holds `accessToken` (in-memory `ref`) and `user`.
- `restoreSession()` сначала пытается использовать текущий access token, иначе делает `POST /auth/refresh`.
- Login/Logout и profile/avatar actions централизованы здесь.
- Поддержка invite continuation через `sessionStorage.pendingInviteToken`.

#### `projects.store`
- `fetchProjects`, `createProject`.
- Lightweight state for project list and loading flag.

#### `board.store` (orchestration-heavy)
- Core aggregate state: `project`, `columns`, `selectedTask`, `members`, `tags`, `activeInvitations`.
- `fetchBoard` параллельно грузит проект, колонки, участников, теги.
- Поддерживает фильтрацию задач (`search`, `assigneeIds`, `tagIds`, `priorities`) на клиенте.
- Handles tasks, columns, invitations, tags, project settings, members management.

### 4) API Client Integration
- Generated client (`KantanoClient`) + custom `AuthorizedHttpRequest` using Axios instance.
- Request interceptor:
  - Prefixes non-absolute URLs with `/api`.
  - Adds `Authorization: Bearer <access_token>` when available.
- Response interceptor:
  - On `401` (except login/refresh), performs refresh via cookie and retries queued requests.

### 5) Module-Level UI Map
- `modules/auth`: login/register forms with `vee-validate` + `zod`.
- `modules/projects`: list/create flow with color picker.
- `modules/board`: kanban UI, drag/drop columns/tasks, task drawer auto-save, board settings dialog.
- `modules/invitations`: invite link/QR generation + accept flow.
- `modules/profile`: profile edit, avatar upload/delete, cookie settings entrypoint.
- `modules/landing`: marketing page.

### 6) Analytics & Consent
- Consent stored in `localStorage` (`kantano-cookie-consent-v1`) and propagated via custom window events.
- Yandex Metrika enabled only when:
  - host is allowed (`kantano.ru`) in prod OR debug mode on localhost;
  - analytics consent granted.
- Router `afterEach` triggers pageview hit when analytics state permits.

### 7) Styling & UX
- Tailwind + PrimeVue overrides + custom CSS.
- Theme switching via `useTheme` toggles `html.dark` and persists in localStorage.
- Vite production build drops `console` and `debugger` via esbuild config.

## Dependencies
- Core: `vue`, `vue-router`, `pinia`, `axios`.
- UI/Forms: `primevue`, `primeicons`, `vee-validate`, `zod`.
- Utility: `@vueuse/core`, `@unhead/vue`, `vue-draggable-plus`.
- Build: `vite`, `tailwindcss`, `openapi-typescript-codegen`.
- Analytics: Yandex Metrika script (`mc.yandex.ru`).

## Risks
- Marketing/runtime mismatch: landing states WebSocket-based realtime while frontend/backend stack currently operates request/response only.
- `board.store` is a large orchestration object (high coupling, potential regression surface).
- Profile email update flow intentionally unavailable in UI until a separate verified flow is designed.

## Open Questions
- Is landing promise about WebSockets intended roadmap or outdated copy?
- Should `board.store` be decomposed into domain-specific stores for maintainability?
- Should profile email update be implemented as a separate verified flow now?

## References
- `frontend/light-task-frontend/src/main.ts:62`
- `frontend/light-task-frontend/src/main.ts:65`
- `frontend/light-task-frontend/src/App.vue:11`
- `frontend/light-task-frontend/src/router/index.ts:18`
- `frontend/light-task-frontend/src/router/index.ts:48`
- `frontend/light-task-frontend/src/router/index.ts:77`
- `frontend/light-task-frontend/src/router/index.ts:91`
- `frontend/light-task-frontend/src/modules/auth/store/auth.store.ts:12`
- `frontend/light-task-frontend/src/modules/auth/store/auth.store.ts:28`
- `frontend/light-task-frontend/src/modules/auth/store/auth.store.ts:46`
- `frontend/light-task-frontend/src/modules/auth/store/auth.store.ts:79`
- `frontend/light-task-frontend/src/modules/projects/store/projects.store.ts:6`
- `frontend/light-task-frontend/src/modules/projects/store/projects.store.ts:12`
- `frontend/light-task-frontend/src/modules/board/store/board.store.ts:30`
- `frontend/light-task-frontend/src/modules/board/store/board.store.ts:62`
- `frontend/light-task-frontend/src/modules/board/store/board.store.ts:113`
- `frontend/light-task-frontend/src/modules/board/store/board.store.ts:276`
- `frontend/light-task-frontend/src/modules/board/store/board.store.ts:350`
- `frontend/light-task-frontend/src/modules/board/store/board.store.ts:373`
- `frontend/light-task-frontend/src/api/config/index.ts:6`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:5`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:9`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:23`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:35`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts:58`
- `frontend/light-task-frontend/src/shared/consent/consent.ts:7`
- `frontend/light-task-frontend/src/shared/consent/consent.ts:48`
- `frontend/light-task-frontend/src/shared/analytics/yandex.ts:12`
- `frontend/light-task-frontend/src/shared/analytics/yandex.ts:13`
- `frontend/light-task-frontend/src/shared/analytics/yandex.ts:238`
- `frontend/light-task-frontend/src/shared/analytics/bootstrap.ts:10`
- `frontend/light-task-frontend/src/shared/analytics/bootstrap.ts:23`
- `frontend/light-task-frontend/src/modules/profile/pages/ProfilePage.vue:131`
- `frontend/light-task-frontend/src/modules/landing/pages/LandingPage.vue:82`
- `frontend/light-task-frontend/.env.template:2`
- `frontend/light-task-frontend/vite.config.ts:35`
- `frontend/light-task-frontend/vite.config.ts:36`
