# Frontend (`frontend/light-task-frontend`)

Vue 3 + TypeScript frontend для Kantano.

## Содержание
- [1. Требования](#1-требования)
- [2. Быстрый старт](#2-быстрый-старт)
- [3. Скрипты](#3-скрипты)
- [4. Переменные окружения](#4-переменные-окружения)
- [5. Генерация API клиента](#5-генерация-api-клиента)
- [6. Analytics Debug (Yandex Metrika)](#6-analytics-debug-yandex-metrika)

## 1. Требования
- Node.js (рекомендуется LTS)
- `pnpm`

## 2. Быстрый старт
```bash
cd frontend/light-task-frontend
pnpm install
cp .env.template .env
pnpm dev
```

Dev URL: `http://localhost:5173`

## 3. Скрипты
```bash
pnpm dev       # запуск dev-сервера
pnpm build     # type-check + production build
pnpm preview   # локальный preview собранного frontend
pnpm gen:api   # перегенерация OpenAPI client
```

## 4. Переменные окружения
`.env.template` содержит:
- `VITE_API_URL` (опционально)

Поведение:
- если `VITE_API_URL` пустой, используется same-origin режим (запросы на `/api`, удобно с proxy/gateway)
- если `VITE_API_URL` задан (например, `http://localhost:8000`), запросы идут на этот backend host

Важно:
- задавай `VITE_API_URL` как base host, без завершающего `/` и без суффикса `/api`

## 5. Генерация API клиента
Клиент генерируется в `src/api/client`:
```bash
cd backend/light_task
uv run python scripts/export_openapi.py

cd ../../frontend/light-task-frontend
pnpm gen:api
```

Сначала обнови `openapi.json` из backend, затем перегенерируй client.

## 6. Analytics Debug (Yandex Metrika)
- в production аналитика включается только для whitelisted host'ов в `src/shared/analytics/yandex.ts`
- на localhost можно временно включить debug:
  - `http://localhost:5173/?analytics_debug=1`
- выключить debug и очистить флаг:
  - `http://localhost:5173/?analytics_debug=0`

Ключ в `localStorage`: `kantano:analytics-debug`.
