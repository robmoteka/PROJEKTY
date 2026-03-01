#!/bin/bash
set -e

echo "Building and starting Postgresql..."
docker compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Generating initial migration for Shell..."
docker compose run --rm shell sh -c "alembic revision --autogenerate -m 'Initial Shell Schema' && alembic upgrade head"

echo "Generating initial migration for Module Issues..."
docker compose run --rm module-issues sh -c "alembic revision --autogenerate -m 'Initial Issues Schema' && alembic upgrade head"

echo "Database initialized successfully!"
