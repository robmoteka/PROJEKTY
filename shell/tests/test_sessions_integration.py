"""
Testy integracyjne sesji użytkownika — pełny przepływ bazy danych.

Testują funkcjonalność sesji bez mockowania FastAPI endpointów:
- Tworzenie, odczyt, walidacja, usuwanie rekordów UserSession
- Interakcja z bazą danych SQLAlchemy
- Logika wygaśnięcia sesji (expires_at)

Baza danych: SQLite in-memory dla szybkości i izolacji.

UWAGA: Testy FastAPI endpointów (/callback, /logout, /) będą obsługiwane
przez E2E testy z Playwright/Cypress, nie tutaj.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db import Base
from models import UserSession

# Baza SQLite in-memory
TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Izolacja — tworzy i niszczy schemat dla każdego testu."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Sesja SQLAlchemy do testów."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------ #
#  Scenariusze: pełny przepływ sesji
# ------------------------------------------------------------------ #


class TestSessionWorkflow:
    """Testy pełnego przepływu sesji w bazie danych."""

    def test_tworzenie_okreslenie_i_sprawdzenie_aktywnej_sesji(
        self, db_session: Session
    ) -> None:
        """
        Przepływ pełnej sesji:
        1. Stwórz UserSession (symulacja /callback)
        2. Wyszukaj i sprawdź czy jest aktywna (symulacja /index)
        3. Usuń (symulacja /logout)
        """
        # --- Krok 1: Tworzenie sesji (po pomyślnej autentykacji OIDC) ---
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(
            session_id="test-session-workflow",
            user_id="user-workflow-001",
            email="workflow@example.com",
            name="Workflow User",
            preferred_username="workflow",
            id_token="eyJ.fake.token",
            expires_at=expires,
        )
        db_session.add(sesja)
        db_session.commit()
        db_session.refresh(sesja)

        # Weryfikacja: sesja została zapisana z ID
        assert sesja.id is not None

        # --- Krok 2: Wyszukanie i weryfikacja sesji (endpoint /) ---
        znaleziona = (
            db_session.query(UserSession)
            .filter(UserSession.session_id == "test-session-workflow")
            .first()
        )
        assert znaleziona is not None
        assert znaleziona.user_id == "user-workflow-001"
        assert znaleziona.email == "workflow@example.com"

        # Sprawdzenie czy sesja nie wygasła
        exp = znaleziona.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        assert exp > datetime.now(timezone.utc), "Sesja powinna być aktywna"

        # --- Krok 3: Usunięcie sesji (symulacja /logout) ---
        db_session.delete(znaleziona)
        db_session.commit()

        # Weryfikacja: rekord został usunięty
        czy_istnieje = (
            db_session.query(UserSession)
            .filter(UserSession.session_id == "test-session-workflow")
            .first()
        )
        assert czy_istnieje is None

    def test_wielu_uzytkownikow_niezalezne_sesje(
        self, db_session: Session
    ) -> None:
        """
        Wiele sesji w bazie to niezależne rekordy — każdy użytkownik
        ma swoją sesję z unikalnym session_id.
        """
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        # Tworzymy 3 sesje dla 3 różnych użytkowników
        sesja1 = UserSession(
            session_id="session-user1",
            user_id="user-1",
            email="user1@example.com",
            expires_at=expires,
        )
        sesja2 = UserSession(
            session_id="session-user2",
            user_id="user-2",
            email="user2@example.com",
            expires_at=expires,
        )
        sesja3 = UserSession(
            session_id="session-user3",
            user_id="user-3",
            email="user3@example.com",
            expires_at=expires,
        )
        db_session.add_all([sesja1, sesja2, sesja3])
        db_session.commit()

        # Weryfikacja: każdy użytkownik ma własną sesję
        wynik_user1 = (
            db_session.query(UserSession)
            .filter(UserSession.session_id == "session-user1")
            .first()
        )
        assert wynik_user1 is not None
        assert wynik_user1.user_id == "user-1"

        wynik_user2 = (
            db_session.query(UserSession)
            .filter(UserSession.session_id == "session-user2")
            .first()
        )
        assert wynik_user2 is not None
        assert wynik_user2.user_id == "user-2"

        # Razem powinno być 3 sesje
        wszystkie = db_session.query(UserSession).all()
        assert len(wszystkie) == 3

    def test_wygasle_sesje_czyszczenie_z_bazy(
        self, db_session: Session
    ) -> None:
        """
        W praktyce: aplikacja sprawdza czy sesja nie wygasła, a jeśli wygasła,
        usuwa ją (cleanup).
        """
        # Tworzymy wygasłą sesję (expires_at w przeszłości)
        expires = datetime.now(timezone.utc) - timedelta(minutes=5)
        wygasla = UserSession(
            session_id="expired-cleanup",
            user_id="user-expired",
            expires_at=expires,
        )
        db_session.add(wygasla)
        db_session.commit()

        # Weryfikacja: sesja istnieje
        znaleziona = (
            db_session.query(UserSession)
            .filter(UserSession.session_id == "expired-cleanup")
            .first()
        )
        assert znaleziona is not None

        # Symulacja cleanup: sprawdzamy czy wygasła i usuwamy
        exp = znaleziona.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp <= datetime.now(timezone.utc):
            # Sesja wygasła — usuwamy
            db_session.delete(znaleziona)
            db_session.commit()

        # Weryfikacja: sesja została usunięta
        po_czyszczeniu = (
            db_session.query(UserSession)
            .filter(UserSession.session_id == "expired-cleanup")
            .first()
        )
        assert po_czyszczeniu is None
