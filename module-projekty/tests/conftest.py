"""
Fixtures wspólne dla wszystkich testów modułu Projekty.

Używa bazy SQLite w pamięci — testy są izolowane od PostgreSQL i mogą działać offline.
Każdy test dostaje czystą bazę (fixture z zakresem "function").
"""

from __future__ import annotations

import os
import sys
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
    Tworzy silnik SQLite in-memory z mapowaniem schematu 'projekty' -> None.

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
    # Stosujemy mapowanie schematu — SQLite nie obsługuje schematów PG
    engine = base_engine.execution_options(schema_translate_map={"projekty": None})
    # Tworzymy wszystkie tabele modułu Projekty
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
    # Fabryka sesji podpięta pod testowy silnik
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
    Dodatkowo patchujemy engine aby startup event nie próbował
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
    # Patchujemy engine używany przez startup event lifespan
    with mock.patch("main.engine", db_engine), mock.patch("db.engine", db_engine):
        with TestClient(app) as test_client:
            yield test_client
    # Czyszczenie nadpisania po teście
    app.dependency_overrides.clear()


@pytest.fixture
def sample_server(db_session: Session):
    """
    Tworzy przykładowy serwer DEV w testowej bazie.

    Używany w testach wymagających istniejącego serwera (relacje FK projektu).
    """
    from crud import create_server
    from schemas import ServerCreate

    # Tworzymy serwer deweloperski z podstawowymi danymi
    server_data = ServerCreate(
        name="DEV-01",
        hostname="192.168.1.100",
        server_type="Dev",
        operating_system="Ubuntu 22.04",
    )
    return create_server(db=db_session, server_data=server_data)


@pytest.fixture
def sample_project(db_session: Session, sample_server):
    """
    Tworzy przykładowy projekt powiązany z serwerem DEV.

    Używany w testach wymagających istniejącego projektu.
    """
    from crud import create_project
    from schemas import ProjectCreate

    # Tworzymy projekt z minimalnym zestawem danych wymaganych przez formularz
    project_data = ProjectCreate(
        name="Testowy Projekt",
        code="TEST-2026",
        owner_name="Jan Kowalski",
        problem_statement="Testowy cel biznesowy",
        dev_server_id=sample_server.id,
    )
    return create_project(db=db_session, project_data=project_data)


@pytest.fixture
def sample_project_with_children(db_session: Session, sample_project):
    """
    Tworzy projekt z kompletem encji potomnych: KPI, technologia, zakres, port.

    Używany w testach weryfikujących kaskadowe usuwanie i widok szczegółów.
    """
    from crud import create_kpi, create_port, create_scope_item, create_technology
    from schemas import KPICreate, PortCreate, ScopeItemCreate, TechnologyCreate

    # KPI — wskaźnik czasu odpowiedzi
    kpi = create_kpi(
        db_session,
        sample_project.id,
        KPICreate(name="Czas odpowiedzi", target_value="< 200ms", unit="ms"),
    )
    # Technologia — FastAPI backend
    tech = create_technology(
        db_session,
        sample_project.id,
        TechnologyCreate(category="Backend", name="FastAPI", version="≥ 0.110.0"),
    )
    # Element zakresu — Must-have CRUD
    scope = create_scope_item(
        db_session,
        sample_project.id,
        ScopeItemCreate(category="Must-have", description="CRUD projektów"),
    )
    # Port sieciowy — API na 8003/TCP
    port = create_port(
        db_session,
        sample_project.id,
        PortCreate(port_number=8003, protocol="TCP", service_name="API"),
    )

    # Zwracamy słownik z wszystkimi encjami
    return {
        "project": sample_project,
        "kpi": kpi,
        "technology": tech,
        "scope_item": scope,
        "port": port,
    }
