# Realtime Testing Strategy

## Goal

Зафиксировать тестовую стратегию для realtime backend так, чтобы:

- тесты были совместимы с CI;
- тесты отражали реальное поведение production-like окружения;
- тесты были базой стиля для остального backend test suite.

## Scope

В рамках этой задачи тестируем только backend.
Frontend automated tests не входят в текущий scope.

## Testing Principles

- Предпочитать integration-first подход.
- Не делать ставку на моки базы данных для доменных realtime flows.
- Не использовать SQLite как замену PostgreSQL.
- Проверять поведение через реальные commit boundaries.
- Проверять websocket и event delivery как часть системы, а не как изолированные функции.

## Test Pyramid

Основной слой:

- integration tests with real PostgreSQL
- integration tests with real Redis
- API and websocket tests against real FastAPI app

Вспомогательный слой:

- unit tests only for small pure logic helpers

## Mandatory Test Infrastructure

- pytest
- pytest-asyncio
- httpx
- test utilities for ASGI lifespan
- real PostgreSQL test database
- real Redis test instance
- Alembic migrations for test schema setup

## Database Strategy

Использовать отдельную test PostgreSQL database.

Правила:

- схема поднимается через миграции;
- application db dependency override указывает на test session;
- данные между тестами очищаются предсказуемо;
- не использовать fake repositories;
- не мокать SQLAlchemy session для integration tests.

## Redis Strategy

Использовать реальный Redis для integration tests.

Правила:

- тесты должны проверять publish and consume behavior;
- тесты должны проверять cross-worker style delivery semantics на уровне EventBus abstraction;
- Redis должен быть поднят в CI services.

## Test Categories

### 1. WebSocket Auth Tests

- successful auth with valid access token
- connection rejected without token
- connection rejected with invalid token
- connection closed on expired token

### 2. Permission Tests

- member can subscribe only to allowed project
- outsider cannot subscribe to project scope
- manager-only events are not delivered to regular members

### 3. Mutation to Event Flow Tests

- create task publishes task.created
- update task publishes task.updated
- move task publishes task.moved
- reorder columns publishes columns.reordered
- update project publishes project.updated
- member removal publishes correct user-scope and project-scope consequences

### 4. Delivery Tests

- subscriber receives event after successful commit
- event is not delivered if mutation fails before commit
- affected user receives project.added_to_user or project.removed_from_user
- delivery works with Redis-backed event propagation assumptions

### 5. Presence Tests

- viewing presence starts and stops correctly
- editing presence starts and stops correctly
- heartbeat keeps presence alive
- TTL clears stale presence

### 6. Edge Case Tests

- user removed while subscribed to project
- reconnect-related resubscribe contract if backend supports it
- project deleted while active subscribers exist

## CI Plan

CI workflow должен:

- checkout repository
- install backend dependencies including test dependencies
- start PostgreSQL service
- start Redis service
- run Alembic migrations against test DB
- run backend tests
- optionally publish coverage later

## Style Rules for Tests

- Тесты должны быть читаемыми и domain-oriented.
- Название теста должно отражать бизнес-сценарий.
- Arrange, Act, Assert должны быть очевидны.
- Не писать чрезмерно хрупкие тесты на внутренние детали реализации.
- Проверять observable behavior.
- Для realtime flows по возможности проверять и response, и DB state, и emitted event.

## Initial Minimum Suite

Первая обязательная волна тестов:

- websocket auth happy path
- websocket auth reject path
- project subscription permission
- task.created event delivery
- task.moved event delivery
- project.updated reflected in user-scope update
- member.removed flow
- invitation event audience restriction

## Definition of Done for Testing

- тесты запускаются локально;
- тесты запускаются в CI;
- тесты не завязаны на developer local DB;
- тесты стабильно покрывают критические realtime сценарии;
- тестовый стиль можно масштабировать на дальнейший backend.
