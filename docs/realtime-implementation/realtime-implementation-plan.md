# Realtime Implementation Plan

## Working Rules

- Source of truth for product behavior: realtime-spec.md
- Source of truth for test approach: realtime-testing-strategy.md
- Если появляется сомнение по продуктовой логике или UX, агент должен остановиться и обсудить это с пользователем до продолжения.
- Если сомнение только техническое и укладывается в spec, агент принимает разумное решение и фиксирует его в Decision Log.
- После завершения каждого этапа агент обновляет этот файл.

## Status Legend

- [ ] not started
- [~] in progress
- [x] done
- [!] blocked

## Phase 0. Design Freeze

- [x] Проверить, что spec и testing strategy не конфликтуют с текущей архитектурой проекта.
- [x] Зафиксировать backend modules и write scope.
- [x] Зафиксировать naming conventions для websocket и Redis channels.
- [x] Зафиксировать event envelope types.
- [x] Зафиксировать список authoritative refetch scenarios.

### Phase 0 Freeze Notes

- Backend write scope:
  `backend/light_task/src/main.py`,
  новый модуль `backend/light_task/src/realtimev1/*`,
  сервисы/роутеры `projects`, `boards`, `tags`, `invitations`,
  `backend/light_task/src/config.py`,
  compose/env/docs и backend tests/CI.
- WebSocket endpoints naming:
  `/ws/user`,
  `/ws/projects/{projectId}`.
- Redis channels naming:
  единый канал `realtime.v1.events` для межворкерного fanout;
  Redis key prefix для presence: `realtime:v1:presence:*`.
- Event envelope type (v1):
  `schemaVersion`, `eventId`, `eventType`, `scope`, `projectId`, `actorUserId`,
  `occurredAt`, `payload`, `clientMutationId?`.
- Authoritative refetch scenarios:
  reconnect/resubscribe,
  access loss (member.removed / project.deleted),
  conflict-prone reorder/move,
  unknown event version,
  local optimistic divergence after failed mutation.

## Phase 1. Backend Realtime Infrastructure

- [x] Добавить websocket entrypoints в backend app.
- [x] Добавить ConnectionManager для local in-memory connections.
- [x] Добавить абстракцию EventBus.
- [x] Добавить Redis Pub/Sub реализацию EventBus.
- [x] Добавить startup/shutdown lifecycle для Redis subscribers.
- [x] Добавить event serialization and deserialization.
- [x] Добавить structured logging around publish and consume.

## Phase 2. Auth and Permission Gating

- [x] Реализовать websocket auth message flow.
- [x] Реализовать validation access token.
- [x] Реализовать access check для /ws/user.
- [x] Реализовать membership check для /ws/projects/{projectId}.
- [x] Реализовать audience filtering для manager-only events.
- [x] Реализовать close behavior для expired or invalid token.

## Phase 3. Event Publishing from Domain Mutations

- [x] Publish project events after successful project mutations.
- [x] Publish member events after successful membership mutations.
- [x] Publish tag events after successful tag mutations.
- [x] Publish board column events after successful column mutations.
- [x] Publish task events after successful task mutations.
- [x] Publish invitation events after successful invitation mutations.
- [x] Publish user-scope project list events to affected users.
- [x] Убедиться, что публикация не происходит до commit.

## Phase 4. Frontend Realtime Layer

- [x] Добавить global realtime manager for authenticated app shell.
- [x] Добавить persistent /ws/user connection.
- [x] Добавить project-scoped connection only on board route.
- [x] Добавить reconnect strategy with backoff.
- [x] Добавить re-auth after refresh flow.
- [x] Добавить offline and reconnecting state.

## Phase 5. Optimistic Sync and Reconciliation

- [x] Встроить optimistic flags into board and project related state.
- [x] Добавить clientMutationId correlation.
- [x] Добавить applyEvent handlers для user-scope событий.
- [x] Добавить applyEvent handlers для project-scope событий.
- [x] Добавить rollback rules for failed mutations.
- [x] Добавить refetch fallback rules for move, reorder, reconnect, access loss.
- [x] Защититься от повторного применения собственного подтвержденного события.

## Phase 6. Soft Presence

- [x] Добавить task viewing presence.
- [x] Добавить task editing presence.
- [x] Добавить heartbeat and TTL.
- [x] Добавить cleanup on close, route leave and disconnect.
- [x] Добавить UI mapping contract for presence banners and indicators.

## Phase 7. Edge Cases

- [x] User removed from active project.
- [x] User role changed while project page is open.
- [x] Project deleted while user is inside.
- [x] Reconnect after temporary network loss.
- [x] Redis unavailable behavior.
- [x] Backend worker fanout validation.

## Phase 8. Backend Tests

- [x] Поднять backend test infrastructure.
- [x] Добавить integration tests for websocket auth.
- [x] Добавить integration tests for permission gating.
- [x] Добавить integration tests for Redis-backed event delivery.
- [x] Добавить integration tests for REST mutation to websocket event flow.
- [x] Добавить integration tests for presence lifecycle.
- [x] Добавить CI workflow for backend tests.

## Phase 9. Release Readiness

- [x] Проверить dev compose setup with Redis.
- [x] Проверить prod compose impact and env requirements.
- [x] Проверить observability and error logging.
- [x] Проверить acceptance criteria from realtime-spec.md.
- [x] Обновить project docs after implementation.

## Decision Log

### Template

- Date:
- Topic:
- Decision:
- Reason:
- Impact:

- Date: 2026-03-24
- Topic: Realtime docs path resolution
- Decision: Использовать `docs/realtime-implementation/*` как source of truth для этой задачи.
- Reason: Файлы из user prompt отсутствуют по корню, но присутствуют в `docs/realtime-implementation/` с теми же именами и содержанием.
- Impact: Реализация и прогресс-трекинг ведутся по этим файлам.

- Date: 2026-03-24
- Topic: Event transport topology
- Decision: Использовать Redis Pub/Sub через единый канал `realtime.v1.events` и internal delivery metadata (user targets / project target / manager-only audience).
- Reason: Упрощает межворкерный fanout без привязки доменных сервисов к Redis и сохраняет единый контракт envelope для клиента.
- Impact: Любой backend worker может публиковать/получать события, локальный ConnectionManager делает финальную фильтрацию.

- Date: 2026-03-24
- Topic: clientMutationId transport
- Decision: Принимать `clientMutationId` из HTTP заголовка `X-Client-Mutation-Id` на mutating REST endpoints.
- Reason: Не меняет текущие request body DTO, сохраняет обратную совместимость и позволяет корреляцию optimistic mutation <-> authoritative event.
- Impact: client может постепенно внедрять correlation без breaking changes в API схемах.

- Date: 2026-03-24
- Topic: Presence transport contract
- Decision: Клиент отправляет presence команды теми же eventType (`task.viewing.started/stopped`, `task.editing.started/stopped`) и heartbeat (`task.presence.heartbeat` с `mode`), сервер рассылает lifecycle + `task.presence.sync`.
- Reason: Минимизирует отдельный protocol surface и упрощает синхронизацию между UI и backend.
- Impact: Presence lifecycle и TTL покрываются единым ws-контрактом без дополнительных REST endpoints.

- Date: 2026-03-24
- Topic: Realtime fallback on frontend
- Decision: Для большинства project-scope событий frontend apply handlers используют authoritative refetch (`fetchBoard`) как fallback-first стратегию, presence обрабатывается инкрементально.
- Reason: Быстрое достижение консистентности v1 без рискованного client-side state reconstruction.
- Impact: Надежная синхронизация состояния при конфликтных сценариях ценой дополнительных запросов.

- Date: 2026-03-24
- Topic: Redis outage degradation mode
- Decision: При ошибке `EventBus.publish` runtime делает fallback на local dispatch; PresenceService работает в fail-open режиме (no-op/snapshot=[]) до восстановления Redis.
- Reason: Не останавливать realtime UX внутри текущего воркера при временной недоступности Redis и не ронять websocket handlers из-за presence Redis ошибок.
- Impact: Межворкерная доставка временно ограничена, но локальные realtime обновления и websocket-поток остаются рабочими; после восстановления Redis сервис автоматически пытается переподключиться через PresenceService.

- Date: 2026-03-24
- Topic: WebSocket envelope serialization
- Decision: Для отправки envelope в websocket использовать `model_dump(mode="json")` (в ConnectionManager и initial presence sync).
- Reason: `ws.send_json` не сериализует Python `datetime`; без JSON-mode происходил `internal_error` при отправке `occurredAt`.
- Impact: Стабильная доставка realtime events/presence sync по websocket без runtime serialization errors.

- Date: 2026-03-24
- Topic: Local integration test execution on Windows
- Decision: Для test mode включить `LIGHTTASK_TESTING=1` и использовать `NullPool` для SQLAlchemy engine; сохранить предсказуемый DB/Redis cleanup fixture; добавить отдельный `docker-compose.test.yml` (test-db/test-redis на отдельных портах) и safety-check против non-test DB/Redis DB 0.
- Reason: На Windows локально воспроизводился loop mismatch (`Future attached to a different loop`) при переиспользовании asyncpg pooled connections между pytest loop и TestClient loop; дополнительно требовалась защита от случайного запуска тестов по dev данным.
- Impact: Локальный integration run стабилен и по умолчанию изолирован от dev-данных; testing strategy (реальный PostgreSQL/Redis + предсказуемая очистка данных между тестами) соблюдается.

- Date: 2026-03-24
- Topic: Frontend dev WebSocket routing
- Decision: Добавить Vite proxy для `/ws` -> backend (`ws: true`) в dev-конфиге.
- Reason: При `VITE_API_URL=` frontend открывал websocket на `ws://localhost:5173/ws/*` без проксирования, из-за чего realtime визуально не работал в локальном dev.
- Impact: В локальной dev-схеме realtime websocket теперь маршрутизируется на backend так же, как `/api`.

- Date: 2026-03-24
- Topic: Drawer live-sync and invitations counters refresh
- Decision: Для `task.updated` применить payload snapshot напрямую в frontend store (включая `selectedTask`), а для manager/owner выполнять `fetchInvitations` на `invitation.created`, `invitation.deleted` и `member.added`.
- Reason: Пользовательский smoke выявил stale-state в открытом task drawer и stale `usedCount` в настройках приглашений; требовалось исправить без расширения event contract.
- Impact: Открытый drawer синхронизируется realtime без переоткрытия при отсутствии локальных несохраненных правок; счетчики приглашений обновляются на релевантных событиях с best-effort refetch.

- Date: 2026-03-24
- Topic: CI-safe JWT key loading for backend tests
- Decision: Добавить фиксированные test JWT ключи в `backend/light_task/tests/fixtures`, выставлять пути к ним в `tests/conftest.py`, а чтение ключей в `src/security.py` перевести на lazy loading с явной ошибкой конфигурации.
- Reason: GitHub Actions падал на import-time с `FileNotFoundError` из-за отсутствия `certs/jwt-private.pem` в CI workspace.
- Impact: `uv run pytest -q` стабильно стартует в CI/локально без зависимости от dev certs, а ошибка конфигурации JWT теперь диагностируется понятным сообщением.

## Open Questions

- None currently.

## Progress Notes

### Template

- Date:
- Phase:
- Done:
- Next:
- Risks:

- Date: 2026-03-24
- Phase: Phase 0. Design Freeze
- Done: Spec/testing strategy сверены с текущей FastAPI + SQLAlchemy архитектурой; зафиксированы write scope, naming conventions, envelope fields и refetch scenarios.
- Next: Реализация Phase 1 (ws entrypoints, connection manager, event bus, Redis subscriber lifecycle, serialization, logging).
- Risks: Основной риск на текущем шаге - аккуратно вшить публикацию событий в существующие сервисы без регресса в текущем REST-поведении.

- Date: 2026-03-24
- Phase: Phase 1-3 (Backend Realtime + Publishing)
- Done: Добавлен `realtimev1` backend слой (ws endpoints, auth gating, connection manager, Redis Pub/Sub bus, presence service, lifecycle), публикация доменных событий после commit встроена в `projects/boards/tags/invitations`.
- Next: Прогон integration tests с реальными PostgreSQL/Redis и валидация edge-case поведения в окружении с несколькими воркерами.
- Risks: Остался риск деградации при Redis outage (поведение не доведено до финального DoD в плане Phase 7).

- Date: 2026-03-24
- Phase: Phase 4-6 (Frontend Realtime + Presence)
- Done: Добавлен frontend realtime manager, user/project ws lifecycle, reconnect/re-auth, clientMutationId headers, applyEvent handlers для user/project scope, presence indicators в карточке и drawer, heartbeat/stop cleanup на закрытии.
- Next: UI/UX polishing и ручная валидация на длинных board-сессиях с высокой частотой событий.
- Risks: Стратегия refetch-first может давать лишнюю сетевую нагрузку на насыщенных досках.

- Date: 2026-03-24
- Phase: Phase 8-9 (Tests/CI/Release prep)
- Done: Добавлен backend integration test suite (`tests/`), pytest infra, CI workflow с PostgreSQL+Redis, compose/env обновлены для Redis и realtime env.
- Next: Полный локальный/CI прогон тестов в окружении с поднятыми сервисами и окончательная checklist-валидация acceptance criteria.
- Risks: В текущем локальном окружении без поднятого PostgreSQL integration tests не могут быть подтверждены end-to-end.

- Date: 2026-03-24
- Phase: Phase 7 + Phase 9 (Edge cases/docs hardening)
- Done: Добавлены runtime/presence graceful degradation при Redis publish/presence ошибках; добавлен integration test для presence fallback и async integration test для Redis fanout между двумя подписчиками; README и backend README обновлены под Redis/realtime test flow.
- Next: Прогнать полный realtime integration suite в окружении с живыми PostgreSQL+Redis (локально после старта Docker daemon или в CI), затем закрыть Phase 7 и acceptance checklist.
- Risks: Локально Docker daemon недоступен, поэтому новые integration тесты пока не подтверждены выполнением в текущей сессии.

- Date: 2026-03-24
- Phase: Phase 7/8/9 validation run
- Done: Подняты `db+redis` через `docker-compose.dev.yml`; пройдены все realtime integration тесты батчами: auth/permission (3/3), mutation/event flow + audience (5/5), presence/fallback/fanout (3/3). Исправлены выявленные runtime issues (ws datetime serialization), test infra stability issues и column response eager-loading для стабильного integration run.
- Next: Финальный acceptance smoke на UI (инициатор без визуальной задержки) и merge/release шаги.
- Risks: Acceptance пункт про perceived UI latency остается ручной проверкой (не покрывается backend integration suite).

- Date: 2026-03-24
- Phase: Test isolation hardening + frontend realtime dev fix
- Done: Добавлен `docker-compose.test.yml`, дефолты тестов переведены на test-порты/DB, добавлены safety-checks (`non-test DB` и `Redis DB 0`), подтвержден smoke run на отдельных test сервисах; в `vite.config.ts` добавлен `/ws` proxy (`ws: true`) для корректного realtime в dev.
- Next: Ручной UI smoke realtime в 2 вкладках на обновленном frontend dev server и финальная acceptance отметка.
- Risks: В этой сессии Playwright-проверка UI ограничена локальными sandbox-правами на запуск Vite процесса; нужна ручная проверка у пользователя.

- Date: 2026-03-24
- Phase: Phase 9 acceptance + test isolation verification
- Done: Через Playwright подтвержден realtime smoke в 2 вкладках для `user-scope` (создание проекта отображается в другой вкладке без refresh) и `project-scope` (добавление колонки отображается в другой вкладке без refresh). Отдельно выполнен полный integration run `uv run pytest -q tests/test_realtime_integration.py` на `docker-compose.test.yml` (`11/11 passed`), и read-only проверка показала, что dev-данные не изменились после тестового прогона.
- Next: Согласовать и выполнить безопасную очистку исторических тестовых записей из dev БД (накоплены до ввода строгой test isolation), затем подготовить финальный merge/release.
- Risks: В dev БД остаются исторические тестовые сущности от прошлых прогонов до полной изоляции; очистка должна быть точечной, чтобы не затронуть реальные пользовательские данные.

- Date: 2026-03-24
- Phase: Frontend realtime polish (drawer + invitations)
- Done: В `board.store` добавлен явный handler для `task.updated` с прямым применением snapshot в `selectedTask`; в `TaskDetailDrawer` добавлена realtime-гидратация формы при внешнем апдейте задачи (с защитой от перезаписи локальных несохраненных изменений). Для manager/owner добавлен refetch приглашений на `invitation.created`, `invitation.deleted`, `member.added`. Typecheck `pnpm exec vue-tsc -b` прошел успешно. Playwright smoke подтвержден для обоих сценариев: (1) описание задачи обновляется в открытом drawer второй вкладки без переоткрытия, (2) `usedCount` приглашения обновляется в открытых настройках после `accept` другим пользователем.
- Next: Подготовка итогового PR/merge по realtime v1.
- Risks: При конкурентном редактировании и несохраненных локальных правках действует non-destructive режим (локальные правки не перетираются автоматически, показывается предупреждение).

- Date: 2026-03-24
- Phase: Phase 8/9 CI hardening
- Done: Исправлен CI crash на старте pytest: тестовое окружение теперь всегда использует ключи из `tests/fixtures`, а `src/security.py` больше не читает JWT файлы на import-time. Полный прогон `uv run pytest -q` локально проходит (`11 passed`).
- Next: Дождаться зеленого GitHub Actions run после пуша fix-коммита и зафиксировать в release notes.
- Risks: Если удалить `tests/fixtures/jwt-*.pem` или переопределить переменные путей несуществующими файлами, тестовый ран всё ещё упадет (теперь с явной диагностикой).
