"""
Testy jednostkowe sesji użytkownika (UserSession).

Testują czystą logikę biznesową bez połączenia z bazą PostgreSQL:
- Tworzenie instancji UserSession z poprawnymi danymi
- Walidacja czasów wygaśnięcia sesji (expired vs aktywna)
- Unikalność wygenerowanych session_id

Baza danych: SQLite in-memory (szybkie, izolowane testy jednostkowe).
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db import Base
from models import UserSession

# Silnik SQLite in-memory — izolowany dla testów jednostkowych
TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db() -> Generator[None, None, None]:
    """Tworzy i usuwa tabele przed każdym testem — pełna izolacja."""
    # Tworzymy schemat bazy w pamięci
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    # Czyścimy schemat po teście — czysta karta dla następnego
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Dostarcza sesję SQLAlchemy dla SQLite in-memory."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------- #
#  Testy: tworzenie UserSession
# --------------------------------------------------------------------------- #


class TestUserSessionCreation:
    """Testy tworzenia rekordów sesji użytkownika."""

    def test_tworzy_sesje_z_poprawnymi_danymi(self, db_session: Session) -> None:
        """
        UserSession powinien być poprawnie zapisany i odczytany z bazy.
        """
        # Przygotowanie: wszystkie wymagane pola sesji
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(
            session_id="abc123session",
            user_id="user-sub-001",
            email="jan@example.com",
            name="Jan Kowalski",
            preferred_username="jkowalski",
            id_token="eyJhbGciOiJSUzI1NiJ9.fake.token",
            expires_at=expires,
        )

        # Działanie: zapis do bazy
        db_session.add(sesja)
        db_session.commit()
        db_session.refresh(sesja)

        # Weryfikacja: poprawny odczyt
        assert sesja.id is not None, "ID powinno być nadane przez bazę"
        assert sesja.session_id == "abc123session"
        assert sesja.user_id == "user-sub-001"
        assert sesja.email == "jan@example.com"
        assert sesja.name == "Jan Kowalski"
        assert sesja.preferred_username == "jkowalski"
        assert sesja.id_token is not None

    def test_opcjonalne_pola_moga_byc_none(self, db_session: Session) -> None:
        """
        Pola email, name, preferred_username i id_token są opcjonalne (nullable).
        """
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(
            session_id="min-session",
            user_id="user-sub-002",
            expires_at=expires,
            # email, name, preferred_username, id_token pominięte
        )

        db_session.add(sesja)
        db_session.commit()
        db_session.refresh(sesja)

        # Wszystkie nullable pola powinny być None
        assert sesja.email is None
        assert sesja.name is None
        assert sesja.preferred_username is None
        assert sesja.id_token is None

    def test_session_id_musi_byc_unikalne(self, db_session: Session) -> None:
        """
        Duplikt session_id powinien powodować błąd bazy danych (UNIQUE constraint).
        """
        from sqlalchemy.exc import IntegrityError

        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        # Pierwszy rekord
        sesja_1 = UserSession(session_id="duplikat", user_id="user-1", expires_at=expires)
        db_session.add(sesja_1)
        db_session.commit()

        # Drugi rekord z tym samym session_id — powinien rzucić IntegrityError
        sesja_2 = UserSession(session_id="duplikat", user_id="user-2", expires_at=expires)
        db_session.add(sesja_2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_wyszukiwanie_sesji_po_session_id(self, db_session: Session) -> None:
        """
        Wyszukanie sesji po session_id powinno zwrócić poprawny rekord.
        """
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(
            session_id="search-target",
            user_id="user-xyz",
            email="x@y.com",
            expires_at=expires,
        )
        db_session.add(sesja)
        db_session.commit()

        # Wyszukujemy po session_id
        wynik = db_session.query(UserSession).filter(
            UserSession.session_id == "search-target"
        ).first()

        assert wynik is not None
        assert wynik.user_id == "user-xyz"
        assert wynik.email == "x@y.com"

    def test_wyszukiwanie_nieistniejacego_session_id_zwraca_none(
        self, db_session: Session
    ) -> None:
        """
        Wyszukanie po nieistniejącym session_id powinno zwrócić None.
        """
        wynik = db_session.query(UserSession).filter(
            UserSession.session_id == "nieistnieje"
        ).first()

        assert wynik is None


# --------------------------------------------------------------------------- #
#  Testy: walidacja czasów wygaśnięcia
# --------------------------------------------------------------------------- #


class TestUserSessionExpiry:
    """Testy logiki wygaśnięcia sesji."""

    def test_aktywna_sesja_expires_at_w_przyszlosci(self, db_session: Session) -> None:
        """
        Sesja z expires_at w przyszłości powinna być uznana za aktywną.
        """
        # expires_at = za 1 godzinę
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(session_id="active", user_id="u1", expires_at=expires)
        db_session.add(sesja)
        db_session.commit()
        db_session.refresh(sesja)

        # Normalizacja do aware datetime (SQLite może zwrócić naive)
        exp = sesja.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        # Sesja jest aktywna — expires_at > teraz
        assert exp > datetime.now(timezone.utc), "Sesja powinna być aktywna"

    def test_wygasla_sesja_expires_at_w_przeszlosci(self, db_session: Session) -> None:
        """
        Sesja z expires_at w przeszłości powinna być uznana za wygasłą.
        """
        # expires_at = 1 godzinę temu
        expires = datetime.now(timezone.utc) - timedelta(hours=1)
        sesja = UserSession(session_id="expired", user_id="u2", expires_at=expires)
        db_session.add(sesja)
        db_session.commit()
        db_session.refresh(sesja)

        # Normalizacja
        exp = sesja.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        # Sesja jest wygasła — expires_at < teraz
        assert exp <= datetime.now(timezone.utc), "Sesja powinna być wygasła"

    def test_usuwanie_wygaslej_sesji(self, db_session: Session) -> None:
        """
        Wygasłą sesję można usunąć z bazy po jej wykryciu.
        """
        expires = datetime.now(timezone.utc) - timedelta(minutes=5)
        sesja = UserSession(session_id="to-delete", user_id="u3", expires_at=expires)
        db_session.add(sesja)
        db_session.commit()

        # Usuwamy wygasłą sesję
        db_session.delete(sesja)
        db_session.commit()

        # Weryfikacja: rekordu nie ma w bazie
        wynik = db_session.query(UserSession).filter(
            UserSession.session_id == "to-delete"
        ).first()
        assert wynik is None


# --------------------------------------------------------------------------- #
#  Testy: generowanie session_id
# --------------------------------------------------------------------------- #


class TestSessionIdGeneration:
    """Testy generowania identyfikatorów sesji."""

    def test_session_id_ma_wystarczajaca_dlugosc(self) -> None:
        """
        secrets.token_urlsafe(64) powinien generować string ≥ 80 znaków.

        Uwaga: token_urlsafe(n) generuje n bajtów base64url → ~4/3 * n znaków.
        64 bajty → ~86 znaków.
        """
        session_id = secrets.token_urlsafe(64)
        # 64 bajty zakodowane base64url to co najmniej 80 znaków
        assert len(session_id) >= 80, f"session_id zbyt krótki: {len(session_id)} znaków"

    def test_session_id_zawiera_tylko_bezpieczne_znaki(self) -> None:
        """
        token_urlsafe powinien zawierać tylko znaki URL-safe (bez + i /).
        """
        for _ in range(20):
            session_id = secrets.token_urlsafe(64)
            # URL-safe base64 używa - i _ zamiast + i /
            assert "+" not in session_id
            assert "/" not in session_id

    def test_generowane_session_id_sa_unikalne(self) -> None:
        """
        Wygenerowane session_id nie powinny się powtarzać (test losowości).

        Przy 1000 generowaniach prawdopodobieństwo kolizji jest astronomicznie małe.
        """
        identyfikatory = {secrets.token_urlsafe(64) for _ in range(1000)}
        # Wszystkie 1000 powinny być różne
        assert len(identyfikatory) == 1000, "Wykryto duplikat session_id!"
