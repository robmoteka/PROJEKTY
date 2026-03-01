#!/bin/bash
set -e

echo "Uruchamianie PostgreSQL..."
docker compose up -d postgres

echo "Oczekiwanie na gotowość PostgreSQL..."
sleep 5

echo "Stosowanie migracji Shell (alembic upgrade head)..."
docker compose run --rm shell sh -c "alembic upgrade head"

echo "Stosowanie migracji Module Issues (alembic upgrade head)..."
docker compose run --rm module-issues sh -c "alembic upgrade head"

echo "Baza danych zainicjalizowana pomyślnie!"
echo ""
echo "Weryfikacja tabel:"
docker compose exec postgres psql -U postgres -d it_os_db -c "\dt"

