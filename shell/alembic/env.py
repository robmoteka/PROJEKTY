from logging.config import fileConfig

from alembic import context  # type: ignore  głupi linter
from sqlalchemy import engine_from_config, pool

# Importuj Base i URL połączenia z modułu db oraz zarejestruj modele w metadanych
from db import Base, DATABASE_URL
import models  # rejestracja modeli w Base.metadata — wymagane dla autogenerate

# Obiekt konfiguracji Alembic
config = context.config

# Konfiguracja logowania z pliku alembic.ini (jeśli plik istnieje)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadane zawierające wszystkie modele modułu Shell — podstawa dla autogenerate
target_metadata = Base.metadata  # type: ignore  głupi linter


def include_name(name: str | None, type_: str, parent_names: dict) -> bool:  # type: ignore[override]
    """
    Filtr schematów dla autogenerate — Alembic zarządza wyłącznie schematem 'shell'.

    Bez tego filtra Alembic skanuje WSZYSTKIE schematy w bazie (keycloak, issues, public)
    i generuje destrukcyjne DROP TABLE dla tabel innych modułów. Filtr ogranicza
    inspekcję bazy wyłącznie do schematu 'shell'.
    """
    if type_ == "schema":
        # Przepuść tylko schemat 'shell' — ignoruj keycloak, issues, public i inne
        return name == "shell"
    # Tabele, indeksy i constrainty — przepuść, SQLAlchemy filtruje przez schemat
    return True


def run_migrations_offline() -> None:
    """Uruchom migracje w trybie offline (bez aktywnego połączenia z bazą)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Tabela wersjonowania Alembic w schemacie shell (nie public)
        version_table="alembic_version_shell",
        version_table_schema="shell",
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Uruchom migracje w trybie online (z aktywnym połączeniem z bazą)."""
    # Nadpisz URL połączenia zmienną środowiskową z docker-compose
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:  # type: ignore  głupi linter
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Tabela wersjonowania Alembic w schemacie shell (nie public)
            version_table="alembic_version_shell",
            version_table_schema="shell",
            include_schemas=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


# Wybór trybu uruchomienia na podstawie flagi Alembic
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
