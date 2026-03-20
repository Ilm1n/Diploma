# Backend (`backend/light_task`)

FastAPI backend для Kantano.

## Содержание
- [1. Состав модуля](#1-состав-модуля)
- [2. Требования](#2-требования)
- [3. Конфигурация](#3-конфигурация)
- [4. Запуск в development](#4-запуск-в-development)
- [5. Запуск без Docker (опционально)](#5-запуск-без-docker-опционально)
- [6. Миграции (Alembic)](#6-миграции-alembic)
- [7. API-проверки (Schemathesis)](#7-api-проверки-schemathesis)
- [8. JWT ключи](#8-jwt-ключи)

## 1. Состав модуля
- точка входа: `src/main.py`
- домены: `auth`, `users`, `projects`, `boards`, `tags`, `invitations`
- миграции: `alembic/`
- контейнеризация: `Dockerfile`, `entrypoint.sh`

## 2. Требования
- Python `>=3.12`
- PostgreSQL 15 (или через Docker Compose из корня проекта)
- RSA key pair для JWT (см. [src/auth/README.md](./src/auth/README.md))
- доступ к S3-compatible bucket (аватары)

## 3. Конфигурация
Backend читает переменные `LIGHTTASK_CONFIG__*` (см. корневой `.env.template`).

Минимально обязательные:
- `LIGHTTASK_CONFIG__DB__USER`
- `LIGHTTASK_CONFIG__DB__PASSWORD`
- `LIGHTTASK_CONFIG__DB__NAME`
- `LIGHTTASK_CONFIG__S3__ACCESS_KEY`
- `LIGHTTASK_CONFIG__S3__SECRET_KEY`
- `LIGHTTASK_CONFIG__S3__BUCKET_NAME`

Важно для localhost:
- `LIGHTTASK_CONFIG__AUTH_JWT__SECURE=False` (иначе refresh-cookie по HTTP не будет работать корректно)

## 4. Запуск в development
Из корня проекта:
```bash
cp .env.template .env
# сгенерируй JWT ключи (см. src/auth/README.md)
docker compose -f docker-compose.dev.yml up --build
```
[src/auth/README.md](./src/auth/README.md)

Доступные endpoint'ы:
- API: `http://127.0.0.1:8000/api/*`
- Health: `http://127.0.0.1:8000/api/health`
- Docs: `http://127.0.0.1:8000/docs`

## 5. Запуск без Docker (опционально)
Из `backend/light_task`:
```bash
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:main_app --host 127.0.0.1 --port 8000 --reload
```

## 6. Миграции (Alembic)
Из `backend/light_task`:
```bash
# применить все миграции
uv run alembic upgrade head

# создать новую миграцию
uv run alembic revision --autogenerate -m "your message"

# откат на 1 шаг
uv run alembic downgrade -1
```

## 7. API-проверки (Schemathesis)
Примеры:
```bash
st run http://127.0.0.1:8000/openapi.json --checks all --max-examples 50
st run http://127.0.0.1:8000/openapi.json --checks all --header "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 8. JWT ключи
Подробная инструкция: [src/auth/README.md](./src/auth/README.md)
