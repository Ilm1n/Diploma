# Yandex Auth Implementation Handoff

## Цель

Добавить в проект `Kantano / LightTask` вход через **Yandex OAuth / Yandex ID** как **дополнительный** способ авторизации, не ломая текущий логин/пароль, и довести решение до состояния:

- backend и frontend работают вместе;
- всё готово к текущему production deploy через GitHub Actions;
- после деплоя можно руками пройти реальный OAuth flow на `https://kantano.ru`.

Это handoff-файл для нового агента/разработчика, который начнёт работу **с нуля**, без контекста прошлой переписки.

---

## Что уже сделано со стороны владельца проекта

Пользователь уже сделал следующее:

- создал приложение в Yandex;
- добавил секреты в GitHub Actions.

Считать это фактом. Следующему агенту **не нужно заново просить** создать Yandex app или добавить secrets, если только не выяснится, что не хватает конкретного значения.

---

## Текущее состояние проекта

### Архитектура

- Backend: `FastAPI + SQLAlchemy async + Alembic`
- Frontend: `Vue 3 + TypeScript + Pinia + Vite`
- База: `PostgreSQL`
- Deploy: Docker + GitHub Actions + VPS

### Production домен

- основной домен: `https://kantano.ru`

### Текущая auth-модель

Сейчас авторизация уже реализована через локальный flow:

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

Поведение:

- backend выдаёт `access token`;
- backend ставит `refresh_token` в `HttpOnly cookie`;
- frontend хранит access token в памяти;
- frontend восстанавливает сессию через `restoreSession()`;
- при `401` frontend делает refresh через cookie.

### Ключевые файлы текущего auth-flow

Backend:

- `backend/light_task/src/auth/router.py`
- `backend/light_task/src/auth/service.py`
- `backend/light_task/src/auth/dependencies.py`
- `backend/light_task/src/security.py`
- `backend/light_task/src/users/models.py`
- `backend/light_task/src/users/service.py`
- `backend/light_task/src/config.py`

Frontend:

- `frontend/light-task-frontend/src/modules/auth/store/auth.store.ts`
- `frontend/light-task-frontend/src/modules/auth/components/LoginPage.vue`
- `frontend/light-task-frontend/src/modules/auth/components/RegisterPage.vue`
- `frontend/light-task-frontend/src/router/index.ts`
- `frontend/light-task-frontend/src/api/config/axios-instance.ts`

Infra / deploy:

- `.github/workflows/deploy.yml`
- `.env.template`
- `.env.prod.template`
- `docker-compose.prod.yml`
- `Caddyfile`
- `backend/light_task/entrypoint.sh`

---

## Что именно нужно реализовать

Нужно добавить **ещё один способ входа**:

- оставить текущий вход по логину/паролю как есть;
- добавить кнопку `Войти через Yandex`;
- после входа через Yandex пользователь должен попадать в тот же локальный session flow, что и обычный пользователь.

Ключевая идея:

- **Yandex используется только как внешний identity provider**;
- после успешного OAuth backend должен выдавать **наши локальные JWT/cookies**, а не менять всю auth-систему.

То есть Yandex login должен в итоге сводиться к:

1. получили профиль Yandex;
2. нашли/создали локального пользователя;
3. выдали локальный `access token`;
4. поставили локальный `refresh_token` cookie;
5. frontend продолжает жить как раньше.

---

## Зафиксированные продуктовые решения

Эти решения уже согласованы с пользователем и **не требуют повторного обсуждения**.

### 1. Старый login/password остаётся

Текущую схему логина/пароля **сохраняем**.  
Yandex login — это только дополнительная опция.

### 2. Flow только через full redirect

Нужен **full redirect flow**, не popup.

### 3. Автолинк существующего пользователя по email

Если при входе через Yandex найден локальный пользователь с тем же email:

- надо автоматически привязать Yandex к существующему локальному аккаунту;
- не делать отдельный экран подтверждения в v1.

### 4. Username стратегия

Для нового пользователя через Yandex:

- `username` брать из Yandex данных;
- основной источник — `login`;
- fallback — `display_name`;
- fallback — local-part email;
- если username занят, добавлять suffix до уникального значения.

### 5. Что тянуть из Yandex профиля

В v1 нужно тянуть:

- `email`
- `username`
- `full_name`

Не нужно в v1:

- avatar import
- управление привязкой/отвязкой в профиле
- отдельный провайдер-менеджмент UI

### 6. Invite flow должен сохраниться

Если пользователь пришёл в login flow из приглашения, нельзя ломать текущее поведение с `pendingInviteToken`.

### 7. Кнопка входа

Нужна **кастомная кнопка** в UI, но с **иконкой Yandex**, визуально как на реальных сайтах.  
Не использовать тяжёлый внешний widget/script, если это не требуется.

---

## Зафиксированные технические решения

### 1. Backend завершает OAuth flow

OAuth callback должен завершаться на backend.

Backend должен:

- получить `code` и `state`;
- обменять `code` на Yandex access token;
- получить профиль пользователя;
- найти/создать локального пользователя;
- поставить локальный `refresh_token` cookie;
- выдать/подготовить локальный `access token`;
- перевести пользователя обратно во frontend.

### 2. Не передавать access token через URL

Это зафиксированное решение.

Нельзя делать схему:

- `redirect /auth/yandex/callback?token=...`

Нужна безопасная схема:

- backend ставит cookie;
- frontend callback page вызывает обычный `restoreSession()`.

### 3. Frontend callback page отдельная

Во frontend нужна отдельная страница / route, которая:

- показывает loading state;
- вызывает `restoreSession()`;
- ведёт пользователя дальше.

### 4. Реальный OAuth smoke-тест локально не обязателен

Мы сознательно не привязываем задачу к полноценной live-проверке OAuth на localhost.

Причина:

- реальный callback удобнее и надёжнее проверять уже после deploy на реальном домене.

Поэтому:

- код и тесты делаем локально;
- реальный OAuth e2e пользователь проверяет руками после deploy.

---

## Что уже известно про Yandex setup

Пользователь уже:

- создал приложение в Yandex;
- добавил GitHub secrets.

Ожидаем, что в секретах уже есть значения уровня:

- `YANDEX_CLIENT_ID`
- `YANDEX_CLIENT_SECRET`
- `YANDEX_REDIRECT_URI`
- `FRONTEND_BASE_URL`

Если имена отличаются, надо подстроить workflow и env contract, но не просить пользователя делать всё заново без необходимости.

Production callback считать таким:

- `https://kantano.ru/api/auth/yandex/callback`

Production frontend base URL считать таким:

- `https://kantano.ru`

---

## Полный implementation plan

## Этап 1. Backend config и зависимости

### Что сделать

Добавить в backend config новый блок для Yandex OAuth.

Минимально нужны поля:

- `client_id`
- `client_secret`
- `redirect_uri`
- `frontend_base_url`

При необходимости можно добавить:

- TTL/secret для `state`
- имя cookie/state namespace

Но не усложнять без пользы.

### Что ещё сделать

Проверить backend dependencies в `backend/light_task/pyproject.toml`.

Если `httpx` сейчас только в dev dependencies — перенести его в runtime dependencies, потому что backend должен во время работы ходить в Yandex API.

---

## Этап 2. Модель пользователя и миграция

### Что изменить в модели пользователя

В `User`:

- сделать `hashed_password` nullable;
- добавить `yandex_id`:
  - nullable;
  - unique;
  - indexed.

### Почему это нужно

Пользователь, пришедший только через Yandex:

- может не иметь локального пароля;
- должен иметь стабильный внешний provider id.

### Как делать миграцию

Важно: миграцию делать **командой Alembic**, а не писать ревизию вручную как основной путь.

Ожидаемый flow:

```bash
cd backend/light_task
uv run alembic revision --autogenerate -m "add yandex auth fields"
```

Потом:

```bash
uv run alembic upgrade head
```

Если autogenerated migration потребует небольшой ручной cleanup, это нормально, но базовый путь — через команду.

---

## Этап 3. Backend OAuth endpoints

Нужно добавить два endpoint:

- `GET /api/auth/yandex/start`
- `GET /api/auth/yandex/callback`

### `/api/auth/yandex/start`

Поведение:

- публичный endpoint;
- принимает optional `next`;
- валидирует `next` как внутренний безопасный путь;
- формирует `state`;
- редиректит пользователя на Yandex authorize URL.

`state` нужен, чтобы:

- не потерять целевой путь после логина;
- защитить flow от подмены.

Решение по `next`:

- разрешать только внутренние относительные пути;
- default — `/projects`.

### `/api/auth/yandex/callback`

Поведение:

- принимает `code` и `state`;
- валидирует `state`;
- меняет `code` на Yandex token;
- запрашивает user info у Yandex;
- находит/создаёт пользователя;
- вызывает существующую логику выдачи локальных токенов;
- редиректит во frontend callback route.

При ошибке:

- не показывать сырой stack trace;
- сделать controlled redirect во frontend, например на `/login?oauth_error=...`.

---

## Этап 4. Логика поиска/создания пользователя

Следующая логика уже согласована и должна быть реализована именно так.

### Порядок поиска пользователя

1. Сначала искать по `yandex_id`
2. Если не найден — искать по `email`
3. Если не найден — создавать нового пользователя

### Если найден по email

Тогда:

- привязать `yandex_id` к существующему пользователю;
- не создавать дубль аккаунта.

### Если создаётся новый пользователь

Тогда:

- `email` ← Yandex email;
- `username` ← Yandex `login`, с fallback'ами;
- `full_name` ← `real_name`, иначе `display_name`;
- `hashed_password = NULL`;
- `yandex_id` заполнить.

### Username strategy

Порядок источников:

1. `login`
2. `display_name`
3. local-part email

После этого:

- нормализовать строку в безопасный username;
- если занято — добавлять suffix до уникальности.

Код должен быть простым и читаемым, без переусложнённой генерации.

---

## Этап 5. Выдача локальной сессии

После успешного Yandex login backend должен использовать **текущий локальный session flow**.

То есть:

- refresh cookie ставится так же, как и при обычном login;
- access token выдаётся так же, как и при обычном login.

Лучший путь:

- переиспользовать существующий `AuthService.set_tokens(...)`, а не дублировать код.

### Важная деталь

Frontend не должен получать access token через query string.

Предпочтительный flow:

1. backend ставит refresh cookie;
2. backend редиректит на SPA route;
3. SPA вызывает `restoreSession()`;
4. SPA получает обычный local access token через refresh endpoint.

Если в ходе реализации окажется, что нужно слегка адаптировать текущий flow для callback-сценария, делать это минимально и без ломки existing auth.

---

## Этап 6. Frontend UI и routing

### Что добавить

На страницы:

- `LoginPage.vue`
- `RegisterPage.vue`

добавить кнопку:

- `Войти через Yandex`

### Как должна работать кнопка

Кнопка делает full-page redirect на backend start endpoint.

Если в `sessionStorage` есть `pendingInviteToken`, передавать `next=/invite/<token>`.

### Новый frontend route

Добавить отдельный route/page:

- `/auth/yandex/callback`

### Поведение callback page

- показать loading state;
- вызвать `authStore.restoreSession()`;
- если success:
  - отправить в `next`, если он есть;
  - иначе в `/projects`;
- если fail:
  - показать toast;
  - отправить на `/login`.

---

## Этап 7. Иконка и кнопка Yandex

### Asset

Рекомендуемый путь:

- `frontend/light-task-frontend/src/assets/images/brand/yandex.svg`

### Формат

- `SVG`

### Рекомендация по размеру

В интерфейсе:

- иконка `18x18` или `20x20`
- высота кнопки около `44px`

### Важное замечание

Если официальный SVG уже есть у пользователя — использовать его.  
Если нет — следующий агент может сам положить корректный SVG ассет в этот путь.

Главное:

- кнопка должна быть кастомной;
- без внешнего widget-flow;
- визуально аккуратной и понятной.

---

## Этап 8. OpenAPI и frontend client

После backend изменений:

1. обновить OpenAPI schema:

```bash
cd backend/light_task
uv run python scripts/export_openapi.py
```

2. перегенерировать frontend API client:

```bash
cd frontend/light-task-frontend
pnpm gen:api
```

Даже если frontend не будет напрямую вызывать эти методы через generated client, schema и client должны оставаться синхронизированными.

---

## Этап 9. CI/CD, env, docs

Нужно обновить:

- `.env.template`
- `.env.prod.template`
- `.github/workflows/deploy.yml`
- README / docs по setup и deploy

### Что должно появиться в env contract

Новые переменные:

- `LIGHTTASK_CONFIG__YANDEX__CLIENT_ID`
- `LIGHTTASK_CONFIG__YANDEX__CLIENT_SECRET`
- `LIGHTTASK_CONFIG__YANDEX__REDIRECT_URI`
- `LIGHTTASK_CONFIG__FRONTEND__BASE_URL`

### Что важно

Пользователь уже сказал, что секреты в GitHub добавлены.  
Значит задача агента:

- аккуратно подцепить их в workflow;
- не заставлять пользователя заново проходить настройку.

---

## Этап 10. Тесты

## Backend tests

Нужно покрыть:

1. новый пользователь создаётся через Yandex;
2. существующий локальный пользователь auto-link по exact email;
3. повторный вход linked user идёт по `yandex_id`;
4. конфликт username разрешается suffix-стратегией;
5. invalid `state`;
6. invalid/expired/ошибочный `code`;
7. Yandex не вернул email;
8. обычный password login всё ещё работает;
9. refresh/logout flow не сломан.

Реальные запросы в Yandex в автотестах не нужны — их мокать.

## Frontend tests

Нужно покрыть:

1. кнопка есть на login page;
2. кнопка есть на register page;
3. callback page вызывает `restoreSession()`;
4. invite continuation не ломается;
5. ошибка OAuth показывает понятный UI/redirect.

## Manual smoke after deploy

После deploy пользователь вручную проверяет:

1. открывает `https://kantano.ru`;
2. нажимает `Войти через Yandex`;
3. проходит OAuth;
4. попадает в проектную часть приложения;
5. logout работает;
6. обычный логин/пароль по-прежнему работает.

---

## Ограничения v1

Что **не надо** делать сейчас:

- unlink Yandex account
- экран управления провайдерами в профиле
- avatar import from Yandex
- отдельный onboarding step для выбора username
- popup-based OAuth flow
- переизобретение всей auth-системы

---

## Порядок реализации

Следующему агенту лучше делать работу в таком порядке:

1. backend config + runtime dependencies;
2. user model changes;
3. Alembic migration;
4. backend Yandex OAuth service/endpoints;
5. backend tests;
6. frontend callback route/page;
7. frontend Yandex buttons;
8. invite continuation integration;
9. OpenAPI export + client regen;
10. env/docs/workflow updates;
11. финальная локальная проверка без реального OAuth e2e;
12. подготовка к ручному smoke after deploy.

Это самый безопасный и наименее хаотичный порядок.

---

## Что нельзя забыть

1. Не ломать существующий login/password flow
2. Не передавать access token через URL
3. Делать migration через Alembic command
4. Сохранять код простым и понятным junior-разработчику
5. Не добавлять лишние абстракции без выгоды
6. Если email от Yandex отсутствует — fail fast и controlled error
7. Пользователь уже настроил Yandex app и GitHub secrets

---

## Официальные источники

При реализации опираться на официальную документацию Yandex ID / OAuth.

Основные ссылки:

- `https://yandex.com/dev/id/doc/en/`
- `https://yandex.com/dev/id/doc/en/register-client`
- `https://yandex.com/dev/id/doc/en/codes/code-url`
- `https://yandex.com/dev/id/doc/en/user-information`
- `https://oauth.yandex.com/`

Также при любой работе с библиотеками/документацией использовать Context7, потому что это явно указано в инструкциях проекта.

---

## Готовый prompt для нового агента

Можно дать новому агенту такой prompt:

> Прочитай `docs/yandex-auth-handoff.md` и начни реализацию входа через Yandex в моём проекте.  
> Важно:
> - не ломать текущий login/password flow;
> - добавить Yandex как дополнительный вход;
> - backend должен завершать OAuth и выдавать текущие локальные JWT/cookies;
> - сделать Alembic migration через команду;
> - подготовить всё к текущему GitHub Actions deploy;
> - код должен быть простой, понятный junior, без лишних усложнений;
> - при необходимости используй Context7 для документации;
> - сначала реализуй backend и миграцию, потом frontend, потом env/docs/tests.

