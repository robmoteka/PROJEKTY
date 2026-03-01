-- Inicjalizacja schematów bazy danych IT Project OS
-- Ten skrypt uruchamia się TYLKO przy pierwszej inicjalizacji bazy (pusty volume).
-- Każdy moduł aplikacji oraz Keycloak otrzymuje własny, izolowany schemat PostgreSQL.

-- Schemat dla Keycloak — wymagany przez serwer tożsamości
CREATE SCHEMA IF NOT EXISTS keycloak;

-- Schemat dla modułu Shell — sesje użytkowników i tabela wersjonowania Alembic
CREATE SCHEMA IF NOT EXISTS shell;

-- Schemat dla modułu Issues — zgłoszenia i tabela wersjonowania Alembic
CREATE SCHEMA IF NOT EXISTS issues;

-- Przyznaj pełne uprawnienia do każdego schematu użytkownikowi PostgreSQL
GRANT ALL ON SCHEMA keycloak TO postgres;
GRANT ALL ON SCHEMA shell TO postgres;
GRANT ALL ON SCHEMA issues TO postgres;
