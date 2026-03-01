"""
Fixtures wspólne dla wszystkich testów modułu Issues.

Używa bazy SQLite w pamięci — testy są izolowane od PostgreSQL i mogą działać offline.
Każdy test dostaje czystą bazę (fixture z zakresem "function").
"""

from __future__ import annotations

import sys
import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Dodajemy katalog modułu do PYTHONPATH — testy uruchamiane z katalogu tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import po ustawieniu ścieżki
from db import Base, get_db  # noqa: E402
from main import app  # noqa: E402

# URL dla SQLite in-memory — każdy test dostaje własną izolowaną bazę
SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_engine():
    """
    Tworzy silnik SQLite in-memory z mapowaniem schematu 'issues' -> None.

    Scope: function — każdy test dostaje świeżą bazę.

    Kluczowe: SQLite in-memory + StaticPool = jedno współdzielone połączenie.
    Bez StaticPool każdy checkout z puli tworzy NOWE puste połączenie in-memory,
    przez co tabele stawiane w create_all są niedostępne dla sesji ORM.
    """
    # StaticPool — wymusza jedno współdzielone połączenie dla wszystkich operacji
    base_engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Stosujemy mapowanie schematu dla całego silnika (dotyczy wszystkich połączeń)
    engine = base_engine.execution_options(schema_translate_map={"issues": None})
    # Tworzymy tabele
    Base.metadata.create_all(bind=engine)
    yield engine
    # Czyszczenie po teście
    Base.metadata.drop_all(bind=engine)
    base_engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    """
    Dostarcza sesję SQLAlchemy połączoną z bazą testową SQLite in-memory.

    Scope: function — sesja zamykana po każdym teście. Silnik już ma
    zastosowane schema_translate_map, więc sesja automatycznie dziedziczy
    mapowanie schematu.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session, db_engine) -> TestClient:
    """
    Dostarcza TestClient FastAPI z nadpisaną zależnością bazy danych.

    Dependency override zamienia prawdziwy get_db na sesję testową SQLite.
    Dodatkowo patchujemy `db.engine` aby startup event nie próbował
    połączyć się z PostgreSQL (który nie jest dostępny poza Dockerem).
    """
    def override_get_db():
        """Nadpisanie get_db — zwraca sesję testową zamiast produkcyjnej."""
        try:
            yield db_session
        finally:
            pass  # Sesja zarządzana przez fixture db_session

    # Nadpisujemy zależność w aplikacji FastAPI
    app.dependency_overrides[get_db] = override_get_db
    # Patchujemy moduł-poziomowy engine używany przez startup event
    # aby nie próbował łączyć się z PostgreSQL poza Dockerem
    with mock.patch("main.engine", db_engine), mock.patch("db.engine", db_engine):
        with TestClient(app) as test_client:
            yield test_client
    # Czyszczenie nadpisania po teście
    app.dependency_overrides.clear()


@pytest.fixture
def sample_issue(db_session: Session):
    """
    Tworzy przykładowe zgłoszenie w bazie testowej.

    Używane w testach wymagających istniejącego rekordu.
    """
    from schemas import IssueCreate
    from crud import create_issue

    issue_data = IssueCreate(
        title="Testowe zgłoszenie",
        description="Opis testowego zgłoszenia",
        priority="Średni",
    )
    issue = create_issue(
        db=db_session,
        issue_data=issue_data,
        author_id="test-user-sub-123",
        author_name="Jan Testowy",
    )
    return issue
