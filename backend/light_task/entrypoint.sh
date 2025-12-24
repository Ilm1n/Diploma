#!/bin/bash

set -e

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "Waiting for postgres at ${DB_HOST}:${DB_PORT}..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done

echo "PostgreSQL started"

echo "Running migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"