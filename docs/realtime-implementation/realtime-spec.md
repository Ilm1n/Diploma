# Realtime Spec v1

## Status

Approved

## Goal

Внедрить realtime-обновления через WebSocket для проекта, доски и списка проектов так, чтобы:

- инициатор видел мгновенный optimistic UI без визуальной задержки;
- остальные пользователи получали обновления почти сразу;
- состояние оставалось консистентным между вкладками, пользователями и backend-воркерами;
- решение работало при нескольких backend-воркерах.

## Scope v1

Входит в scope:

- realtime для доски: колонки, задачи, move, reorder, обновление карточек;
- realtime для проекта: настройки проекта, участники, роли, теги;
- realtime для списка проектов пользователя;
- realtime для инвайтов только для manager/owner;
- soft presence на уровне задачи: viewing и editing;
- optimistic UI на фронте;
- authoritative reconciliation через websocket events и refetch fallback;
- backend test coverage для realtime и event flow;
- CI-friendly backend tests.

Не входит в scope:

- курсоры;
- typing по символам;
- hard lock редактирования;
- durable event log;
- replay пропущенных событий;
- frontend test suite в рамках данной задачи.

## Transport and Infra

- Использовать WebSocket.
- Использовать Redis Pub/Sub для межворкерного обмена событиями.
- На каждом backend-воркере должен быть локальный ConnectionManager.
- Доменные сервисы не должны зависеть от Redis напрямую.
- Публикация событий должна происходить только после успешного commit.

## Channels

### /ws/user

Глобальный websocket для авторизованного пользователя.
Назначение:

- обновление списка проектов;
- уведомления о добавлении или удалении из проекта;
- обновления project list item;
- user-scope события.

### /ws/projects/{projectId}

WebSocket для конкретного проекта.
Назначение:

- board events;
- project events;
- member and tag events;
- invitation events для manager/owner;
- task soft presence.

## Authentication

- Клиент открывает websocket-соединение.
- Первым сообщением отправляет auth с access token.
- Сервер валидирует access token.
- Для project-scope дополнительно валидируется доступ к проекту.
- При невалидном или истекшем токене сервер закрывает соединение.
- Клиент обновляет access token через существующий HTTP refresh flow и переподключается.

## Client Model

Базовый принцип:

- optimistic UI обязателен;
- websocket event является authoritative confirmation или external update;
- refetch fallback обязателен для сложных и конфликтных случаев.

Правила:

- локальный state меняется сразу;
- сущность помечается как pending или syncing;
- mutation уходит по REST;
- после commit сервер публикует событие;
- клиент различает собственное подтверждение и внешнее событие через clientMutationId;
- при ошибке выполняется rollback или refetch;
- при reconnect выполняется refetch нужных срезов данных.

## Event Envelope

Каждое событие должно содержать:

- schemaVersion
- eventId
- eventType
- scope
- projectId
- actorUserId
- occurredAt
- payload
- clientMutationId optional

Начальная версия:

- schemaVersion = 1

## Event Catalog

### User-scope events

- project.added_to_user
- project.removed_from_user
- project.list_item_updated

### Project-scope events

- project.updated
- project.deleted
- member.added
- member.role_changed
- member.removed
- tag.created
- tag.updated
- tag.deleted
- column.created
- column.updated
- column.deleted
- columns.reordered
- task.created
- task.updated
- task.deleted
- task.moved

### Manager-only events

- invitation.created
- invitation.deleted

### Presence events

- task.viewing.started
- task.viewing.stopped
- task.editing.started
- task.editing.stopped
- task.presence.sync

## Payload Policy

Для v1:

- task.updated должен передавать полный snapshot задачи;
- сложные события должны передавать authoritative payload;
- client не должен пытаться вычислять серверное финальное состояние там, где это уже делает backend.

## Presence Model

Soft presence only.
Правила:

- presence не блокирует редактирование;
- viewing означает открытие карточки;
- editing означает начало редактирования полей;
- состояние presence поддерживается heartbeat + TTL;
- UI показывает предупреждение, но не hard lock.

UI expectations:

- на карточке задачи допускается компактный индикатор;
- в drawer должен быть заметный баннер о том, что задачу уже редактируют.

## updatedAt Policy

Любое видимое изменение проекта должно обновлять project.updatedAt.
Включает:

- задачи;
- колонки;
- теги;
- участников;
- роли;
- настройки проекта;
- инвайты.

## Critical Flows

- Если пользователя удалили из проекта, он должен получить событие, увидеть уведомление и быть перенаправлен на список проектов.
- Если проект удален, пользователь должен покинуть project-scope и получить корректный redirect.
- После reconnect состояние синхронизируется через refetch.
- При нескольких backend-воркерах событие должно доходить независимо от того, какой воркер обработал mutation.

## Acceptance Criteria

- Изменения одного пользователя видны другим без ручного refresh.
- Initiator не видит визуальной задержки на drag, rename, update.
- Сложные конфликты не приводят к устойчивому рассинхрону.
- Решение работает через Redis при нескольких воркерах.
- Presence появляется и исчезает корректно.
- User removal from project синхронизируется в realtime.
- Список проектов live-обновляется и корректно пересортировывается.
