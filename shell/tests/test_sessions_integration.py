"""
Testy integracyjne sesji użytkownika — endpointy /callback, /logout, /.

Testują pełny przepływ z bazą danych SQLite in-memory:
- /callback sukces → tworzy rekord w DB, ustawia session_id w cookie (NIE JWT!)
- /logout → usuwa rekord z DB, kasuje cookie
- Strona główna z poprawnym session_id → wyświetla dane użytkownika
- Strona główna z wygasłym session_id → traktuje jak niezalogowany

Strategia:
- OIDCService i verify_id_token są mockowane (brak Keycloak)
- `get_db` jest nadpisywane przez FastAPI dependency override → SQLite in-memory
- Testy sprawdzają zarówno zachowanie HTTP jak i stan bazy danych
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from unittest.mock import AsyncMock, MagicMock, patch

from config import Settings
from db import Base
from models import UserSession

# ------------------------------------------------------------------ #
#  Ustawienia testowe
# ------------------------------------------------------------------ #

TEST_SETTINGS = Settings(
    OIDC_ISSUER="https://keycloak.test/realms/it-os",
    OIDC_CLIENT_ID="shell-test",
    OIDC_CLIENT_SECRET="test-secret",
    OIDC_REDIRECT_URI="http://testserver/callback",
    JWT_ALGORITHM="RS256",
    SESSION_COOKIE_NAME="session",
    SESSION_COOKIE_MAX_AGE=3600,
    SECRET_KEY="test-only-secret",
    POSTGRES_HOST="localhost",
    CORS_ORIGINS="http://localhost:5050",
)

# Przykładowe claims po walidacji id_token (zwracane przez mock verify_id_token)
FAKE_CLAIMS: dict[str, Any] = {
    "sub": "user-abc-123",
    "email": "test@example.com",
    "name": "Test User",
    "preferred_username": "testuser",
    "iss": TEST_SETTINGS.OIDC_ISSUER,
    "aud": TEST_SETTINGS.OIDC_CLIENT_ID,
    "exp": int(time.time()) + 3600,
}

# ------------------------------------------------------------------ #
#  Baza danych: SQLite in-memory dla testów
# ------------------------------------------------------------------ #

TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def get_test_db() -> Generator[Session, None, None]:
    """Dependency override — zamiast PostgreSQL używa SQLite in-memory."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------ #
#  Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Tworzy i usuwa schemat przed każdym testem — pełna izolacja."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    AsyncClient z transportem ASGI oraz nadpisaną dependency `get_db`.

    Wszystkie zewnętrzne zależności (OIDC, PostgreSQL) są zamockowane.
    """
    with (
        patch("main.Base.metadata.create_all"),
        patch("main.get_settings", return_value=TEST_SETTINGS),
        patch("auth.router.get_settings", return_value=TEST_SETTINGS),
        patch("dependencies.get_settings", return_value=TEST_SETTINGS),
    ):
        from main import app
        from db import get_db

        # Nadpisujemy get_db — zamiast PostgreSQL używamy SQLite in-memory
        app.dependency_overrides[get_db] = get_test_db

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            follow_redirects=False,
        ) as ac:
            yield ac

        # Sprzątamy po teście
        app.dependency_overrides.clear()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Sesja SQLAlchemy do bezpośredniej weryfikacji stanu bazy w testach."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------ #
#  Testy: /callback — tworzenie sesji
# ------------------------------------------------------------------ #


class TestCallbackEndpointSesje:
    """Testy endpointu /callback — tworzenie sesji server-side."""

    @pytest.mark.asyncio
    async def test_callback_tworzy_rekord_w_db(
        self, client: AsyncClient, db_session: Session
    ) -> None:
        """
        Pomyślny /callback powinien stworzyć rekord UserSession w bazie danych.
        Cookie powinno zawierać session_id (losowy string), NIE token JWT.
        """
        fake_tokens = {"id_token": "eyJ.fake.token", "access_token": "access123"}

        with (
            patch("auth.router.OIDCService") as mock_cls,
            patch("auth.router.verify_id_token", return_value=FAKE_CLAIMS),
            patch("auth.router.extract_user_info", return_value={
                "sub": "user-abc-123",
                "email": "test@example.com",
                "name": "Test User",
                "preferred_username": "testuser",
            }),
        ):
            # Konfigurujemy mock OIDCService
            mock_svc = AsyncMock()
            mock_svc.exchange_code_for_tokens.return_value = fake_tokens
            mock_svc.get_jwks.return_value = {"keys": []}
            mock_cls.return_value = mock_svc

            # Wysyłamy żądanie z poprawnym state w cookie
            response = await client.get(
                "/callback?code=authcode123&state=mystate",
                cookies={"oidc_state": "mystate"},
            )

        # Oczekujemy przekierowania na /
        assert response.status_code == 302
        assert response.headers["location"] == "/"

        # Cookie musi istnieć i zawierać session_id (nie JWT!)
        session_cookie = response.cookies.get("session")
        assert session_cookie is not None, "Cookie 'session' powinno być ustawione"
        # session_id to URL-safe base64 — NIE format JWT (brak kropek)
        assert "." not in session_cookie or session_cookie.count(".") < 2, (
            "Cookie nie powinno zawierać raw JWT (brak trzech segmentów)"
        )

        # Weryfikacja: rekord istnieje w bazie danych
        db_record = db_session.query(UserSession).filter(
            UserSession.session_id == session_cookie
        ).first()
        assert db_record is not None, "Rekord sesji powinien istnieć w DB"
        assert db_record.user_id == "user-abc-123"
        assert db_record.email == "test@example.com"
        assert db_record.name == "Test User"

    @pytest.mark.asyncio
    async def test_callback_bledny_state_nie_tworzy_sesji(
        self, client: AsyncClient, db_session: Session
    ) -> None:
        """
        Niezgodność state (CSRF) powinna zwrócić 400 i nie tworzyć sesji w DB.
        """
        response = await client.get(
            "/callback?code=authcode&state=inny-state",
            cookies={"oidc_state": "poprawny-state"},
        )

        # Oczekujemy błędu 400
        assert response.status_code == 400

        # Baza powinna być pusta — nie stworzono sesji
        count = db_session.query(UserSession).count()
        assert count == 0, "Przy błędzie CSRF nie powinno być rekordów w DB"


# ------------------------------------------------------------------ #
#  Testy: /logout — usuwanie sesji
# ------------------------------------------------------------------ #


class TestLogoutEndpointSesje:
    """Testy endpointu /logout — usuwanie sesji server-side."""

    @pytest.mark.asyncio
    async def test_logout_usuwa_rekord_z_db(
        self, client: AsyncClient, db_session: Session
    ) -> None:
        """
        /logout powinien usunąć rekord UserSession z bazy i skasować cookie.
        """
        # Przygotowanie: tworzymy sesję w bazie bezpośrednio
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(
            session_id="test-session-to-logout",
            user_id="user-abc-123",
            email="test@example.com",
            id_token="eyJ.fake.token",
            expires_at=expires,
        )
        db_session.add(sesja)
        db_session.commit()

        # Weryfikacja: rekord istnieje przed wylogowaniem
        assert db_session.query(UserSession).count() == 1

        with patch("auth.router.OIDCService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_end_session_url.return_value = "https://keycloak.test/logout"
            mock_cls.return_value = mock_svc

            response = await client.get(
                "/logout",
                cookies={"session": "test-session-to-logout"},
            )

        # Oczekujemy przekierowania do OIDC end_session_endpoint
        assert response.status_code == 302

        # Rekord powinien być usunięty z bazy
        db_session.expire_all()  # Odświeżamy cache sesji SQLAlchemy
        count = db_session.query(UserSession).count()
        assert count == 0, "Rekord sesji powinien być usunięty po wylogowaniu"

    @pytest.mark.asyncio
    async def test_logout_bez_cookie_nie_kraszuje(
        self, client: AsyncClient
    ) -> None:
        """
        /logout bez cookie sesji powinien działać bez błędu (graceful logout).
        """
        with patch("auth.router.OIDCService") as mock_cls:
            mock_svc = AsyncMock()
            mock_svc.get_end_session_url.return_value = "https://keycloak.test/logout"
            mock_cls.return_value = mock_svc

            response = await client.get("/logout")

        # Mimo braku cookie — przekierowanie działa
        assert response.status_code == 302


# ------------------------------------------------------------------ #
#  Testy: strona główna z sesją / bez sesji
# ------------------------------------------------------------------ #


class TestIndexEndpointSesje:
    """Testy endpointu / — weryfikacja stanu zalogowania przez sesję DB."""

    @pytest.mark.asyncio
    async def test_strona_glowna_z_aktywna_sesja(
        self, client: AsyncClient, db_session: Session
    ) -> None:
        """
        Strona główna z poprawnym session_id → użytkownik jest rozpoznany.
        """
        # Wstawiamy aktywną sesję do bazy
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        sesja = UserSession(
            session_id="valid-session-123",
            user_id="user-abc",
            email="logged@example.com",
            name="Zalogowany Użytkownik",
            preferred_username="zalogowany",
            expires_at=expires,
        )
        db_session.add(sesja)
        db_session.commit()

        # Żądanie ze strony zalogowanego użytkownika
        response = await client.get("/", cookies={"session": "valid-session-123"})

        assert response.status_code == 200
        # Strona powinna zawierać dane użytkownika
        assert "Zalogowany Użytkownik" in response.text or "zalogowany" in response.text

    @pytest.mark.asyncio
    async def test_strona_glowna_z_wygasla_sesja(
        self, client: AsyncClient, db_session: Session
    ) -> None:
        """
        Strona główna z wygasłym session_id → użytkownik traktowany jako niezalogowany.
        Wygasła sesja powinna być automatycznie usunięta z bazy.
        """
        # Wstawiamy wygasłą sesję do bazy (expires_at w przeszłości)
        expires = datetime.now(timezone.utc) - timedelta(hours=1)
        sesja = UserSession(
            session_id="expired-session-456",
            user_id="user-xyz",
            email="expired@example.com",
            expires_at=expires,
        )
        db_session.add(sesja)
        db_session.commit()

        # Żądanie z wygasłym session_id
        response = await client.get("/", cookies={"session": "expired-session-456"})

        # Strona zwraca 200, ale użytkownik jest niezalogowany
        assert response.status_code == 200

        # Wygasła sesja powinna być usunięta z bazy przez get_current_user
        db_session.expire_all()
        count = db_session.query(UserSession).filter(
            UserSession.session_id == "expired-session-456"
        ).count()
        assert count == 0, "Wygasła sesja powinna być usunięta z DB"

    @pytest.mark.asyncio
    async def test_strona_glowna_bez_sesji(self, client: AsyncClient) -> None:
        """
        Strona główna bez cookie sesji → zwraca 200 jako niezalogowany użytkownik.
        """
        response = await client.get("/")
        assert response.status_code == 200
