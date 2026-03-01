"""
Testy jednostkowe dla warstwy bazy danych (shell/db.py).

Testują konfigurację połączenia z bazą i zachowanie dependency get_db()
BEZ wymaganego połączenia z PostgreSQL — wszystkie wywołania silnika są mockowane.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from config import Settings


# ---------------------------------------------------------------------------
# Testy Settings.DATABASE_URL
# ---------------------------------------------------------------------------


class TestSettingsDatabaseUrl:
    """Testy właściwości DATABASE_URL klasy Settings."""

    def test_database_url_format_domyslny(self) -> None:
        """DATABASE_URL ma poprawny format postgresql://user:pass@host:port/db."""
        # Tworzymy Settings z domyślnymi wartościami (bez pliku .env)
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            POSTGRES_USER="testuser",
            POSTGRES_PASSWORD="testpass",
            POSTGRES_HOST="localhost",
            POSTGRES_PORT="5432",
            POSTGRES_DB="testdb",
        )

        url = settings.DATABASE_URL

        # Sprawdzamy czy URL ma poprawny format
        assert url == "postgresql://testuser:testpass@localhost:5432/testdb"

    def test_database_url_zawiera_protokol(self) -> None:
        """DATABASE_URL musi zaczynać się od postgresql://."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )

        assert settings.DATABASE_URL.startswith("postgresql://")

    def test_database_url_zawiera_host_i_port(self) -> None:
        """DATABASE_URL zawiera host i port z ustawień."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            POSTGRES_HOST="my-db-host",
            POSTGRES_PORT="5433",
        )

        url = settings.DATABASE_URL

        assert "my-db-host" in url
        assert "5433" in url

    def test_database_url_zawiera_nazwe_bazy(self) -> None:
        """DATABASE_URL zawiera nazwę bazy danych na końcu ścieżki."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            POSTGRES_DB="moja_baza",
        )

        assert settings.DATABASE_URL.endswith("/moja_baza")

    def test_database_url_koduje_haslo_specjalne_znaki(self) -> None:
        """DATABASE_URL poprawnie zawiera hasło (bez enkodowania — SQLAlchemy obsługuje to sam)."""
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            POSTGRES_PASSWORD="tajne_haslo_123",
        )

        # Hasło musi być obecne w URL
        assert "tajne_haslo_123" in settings.DATABASE_URL


# ---------------------------------------------------------------------------
# Testy get_db() — dependency FastAPI
# ---------------------------------------------------------------------------


class TestGetDb:
    """Testy generatora get_db() — dependency wstrzykiwana w endpointach FastAPI."""

    def test_get_db_zwraca_sesje(self) -> None:
        """get_db() jako generator musi zwrócić obiekt sesji przez yield."""
        # Importujemy dopiero tutaj, żeby patch na engine zadziałał
        from db import get_db

        # Mockujemy SessionLocal, żeby nie łączyć się z prawdziwą bazą
        mock_session = MagicMock()

        # Patch SessionLocal w module db
        with patch("db.SessionLocal", return_value=mock_session):
            # Pobieramy generator
            gen = get_db()
            # Pierwszy next() powinien zwrócić sesję (yield db)
            session = next(gen)

            assert session is mock_session

    def test_get_db_zamyka_sesje_po_zakonczeniu(self) -> None:
        """get_db() musi wywołać db.close() po wyczerpaniu generatora."""
        from db import get_db

        mock_session = MagicMock()

        with patch("db.SessionLocal", return_value=mock_session):
            gen = get_db()
            next(gen)  # yield db

            # Wyczerpujemy generator (blok finally powinien wywołać close())
            with pytest.raises(StopIteration):
                next(gen)

            # Sprawdzamy, że close() zostało wywołane dokładnie raz
            mock_session.close.assert_called_once()

    def test_get_db_zamyka_sesje_przy_wyjatku(self) -> None:
        """get_db() musi zamknąć sesję nawet jeśli w endpoincie wystąpił wyjątek."""
        from db import get_db

        mock_session = MagicMock()

        with patch("db.SessionLocal", return_value=mock_session):
            gen = get_db()
            next(gen)  # yield db

            # Symulujemy wyjątek wewnątrz endpointu (throw do generatora)
            with pytest.raises(ValueError):
                gen.throw(ValueError("błąd w endpoincie"))

            # Mimo wyjątku close() musi zostać wywołane (blok finally)
            mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# Testy modelu UserSession — walidacja kolumn
# ---------------------------------------------------------------------------


class TestUserSessionModel:
    """Testy struktury modelu ORM UserSession."""

    def test_usersession_ma_wymagane_kolumny(self) -> None:
        """Model UserSession musi posiadać wszystkie kolumny wymagane przez schemat."""
        from models import UserSession

        # Pobieramy nazwy kolumn z metadanych tabeli
        kolumny = {col.name for col in UserSession.__table__.columns}

        wymagane = {
            "id",
            "session_id",
            "user_id",
            "email",
            "name",
            "preferred_username",
            "id_token",
            "created_at",
            "expires_at",
        }

        assert wymagane.issubset(kolumny), (
            f"Brakujące kolumny: {wymagane - kolumny}"
        )

    def test_usersession_session_id_unikalny(self) -> None:
        """Kolumna session_id musi mieć constraint UNIQUE."""
        from models import UserSession

        session_id_col = UserSession.__table__.columns["session_id"]

        assert session_id_col.unique is True

    def test_usersession_user_id_not_nullable(self) -> None:
        """Kolumna user_id nie może być NULL — każda sesja ma właściciela."""
        from models import UserSession

        user_id_col = UserSession.__table__.columns["user_id"]

        assert user_id_col.nullable is False

    def test_usersession_nazwa_tabeli(self) -> None:
        """Model UserSession musi mapować na tabelę 'sessions'."""
        from models import UserSession

        assert UserSession.__tablename__ == "sessions"
