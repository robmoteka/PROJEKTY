"""
Testy integracyjne middleware — error handling i CORS.

Testują zachowanie aplikacji przy błędach HTTP i konfigurację CORS:
- Request HTMX z HTTPException → zwraca HTML partial z klasą 'alert-error'
- Request nie-HTMX z HTTPException → zwraca JSON z polem 'detail'
- Request HTMX z błędem 500 (nieobsłużony wyjątek) → HTML partial z komunikatem
- CORS preflight (OPTIONS) → poprawne nagłówki Access-Control-*

Strategia:
- Do aplikacji dodajemy tymczasowy testowy endpoint /test-error, który rzuca
  HTTPException lub generyczny wyjątek, by wywołać handlery middleware.
"""

from __future__ import annotations

from typing import Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import Settings
from db import Base

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
    # Dwa origins do testowania CORS
    CORS_ORIGINS="http://localhost:5050,http://localhost:8001",
)

# SQLite in-memory
TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def get_test_db() -> Generator[Session, None, None]:
    """Dependency override dla bazy danych."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Izolacja bazy — tworzy i niszczy schemat przed każdym testem."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    AsyncClient z przetestowaną konfigurację middleware i pomocniczymi endpointami.

    Dodaje dwa testowe endpointy:
    - GET /test-http-error  — rzuca HTTPException 404
    - GET /test-server-error — rzuca generyczny RuntimeError (status 500)
    """
    with (
        patch("main.Base.metadata.create_all"),
        patch("main.get_settings", return_value=TEST_SETTINGS),
        patch("auth.router.get_settings", return_value=TEST_SETTINGS),
        patch("dependencies.get_settings", return_value=TEST_SETTINGS),
    ):
        from main import app
        from db import get_db

        # Nadpisujemy get_db → SQLite in-memory
        app.dependency_overrides[get_db] = get_test_db

        # Pomocniczy endpoint: HTTP 404
        @app.get("/test-http-error")
        async def raise_http_error() -> None:
            raise HTTPException(status_code=404, detail="Zasób nie istnieje")

        # Pomocniczy endpoint: nieobsłużony wyjątek (status 500)
        @app.get("/test-server-error")
        async def raise_server_error() -> None:
            raise RuntimeError("Krytyczny błąd serwera — tylko w testach!")

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            follow_redirects=False,
        ) as ac:
            yield ac

        app.dependency_overrides.clear()
        # Usuwamy testowe endpointy z routera (sprzątanie)
        app.routes[:] = [
            r for r in app.routes
            if getattr(r, "path", None) not in ("/test-http-error", "/test-server-error")
        ]


# ------------------------------------------------------------------ #
#  Testy: HTTPException — HTMX vs REST
# ------------------------------------------------------------------ #


class TestHttpExceptionHandler:
    """Testy global error handlera dla HTTPException."""

    @pytest.mark.asyncio
    async def test_htmx_request_zwraca_html_partial(
        self, client: AsyncClient
    ) -> None:
        """
        Request HTMX (nagłówek HX-Request: true) z HTTPException
        powinien zwrócić HTML partial z klasą 'alert-error'.
        """
        response = await client.get(
            "/test-http-error",
            headers={"HX-Request": "true"},
        )

        # Status zgodny z wyjątkiem
        assert response.status_code == 404

        # Odpowiedź to HTML, nie JSON
        assert "text/html" in response.headers.get("content-type", "")

        # Partial zawiera klasę DaisyUI alert-error
        assert "alert-error" in response.text

        # Partial zawiera komunikat z wyjątku
        assert "Zasób nie istnieje" in response.text

    @pytest.mark.asyncio
    async def test_rest_request_zwraca_json(self, client: AsyncClient) -> None:
        """
        Zwykły request (bez nagłówka HX-Request) z HTTPException
        powinien zwrócić JSON z polem 'detail'.
        """
        response = await client.get("/test-http-error")
        # Brak nagłówka HX-Request — zwykły REST request

        assert response.status_code == 404

        # Odpowiedź to JSON
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Zasób nie istnieje"

    @pytest.mark.asyncio
    async def test_htmx_error_partial_nie_jest_pelnym_html(
        self, client: AsyncClient
    ) -> None:
        """
        Partial HTMX nie powinien zawierać znaczników <html>, <head>, <body>.
        Musi być fragmentem HTML gotowym do wstrzyknięcia przez HTMX swap.
        """
        response = await client.get(
            "/test-http-error",
            headers={"HX-Request": "true"},
        )

        # Brak struktury pełnego HTML dokumentu
        assert "<html" not in response.text.lower()
        assert "<head" not in response.text.lower()
        assert "<body" not in response.text.lower()


# ------------------------------------------------------------------ #
#  Testy: generyczny handler (status 500)
# ------------------------------------------------------------------ #


class TestGenericExceptionHandler:
    """Testy catch-all handlera dla nieobsłużonych wyjątków (status 500)."""

    @pytest.mark.asyncio
    async def test_htmx_server_error_zwraca_html_500(
        self, client: AsyncClient
    ) -> None:
        """
        Nieobsłużony wyjątek przy HTMX request powinien zwrócić HTML partial, status 500.
        """
        response = await client.get(
            "/test-server-error",
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 500
        assert "text/html" in response.headers.get("content-type", "")
        assert "alert-error" in response.text

    @pytest.mark.asyncio
    async def test_rest_server_error_zwraca_json_500(
        self, client: AsyncClient
    ) -> None:
        """
        Nieobsłużony wyjątek przy zwykłym request powinien zwrócić JSON, status 500.
        """
        response = await client.get("/test-server-error")

        assert response.status_code == 500
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_server_error_nie_ujawnia_stacktrace(
        self, client: AsyncClient
    ) -> None:
        """
        Odpowiedź na błąd 500 nie może zawierać szczegółów implementacji
        (ochrona przed information disclosure).
        """
        response = await client.get("/test-server-error")

        # Stack trace ani nazwa wyjątku nie mogą trafić do klienta
        assert "RuntimeError" not in response.text
        assert "Traceback" not in response.text
        assert "krytyczny błąd serwera" not in response.text.lower()


# ------------------------------------------------------------------ #
#  Testy: CORS
# ------------------------------------------------------------------ #


class TestCorsMiddleware:
    """Testy konfiguracji CORS — nagłówki dla requestów cross-origin."""

    @pytest.mark.asyncio
    async def test_cors_preflight_dozwolony_origin(
        self, client: AsyncClient
    ) -> None:
        """
        OPTIONS request z dozwolonym Origin powinien zwrócić poprawne
        nagłówki CORS (Access-Control-Allow-*).
        """
        response = await client.options(
            "/",
            headers={
                "Origin": "http://localhost:5050",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Dozwolony origin — brak blokady
        assert response.headers.get("access-control-allow-origin") in (
            "http://localhost:5050",
            "*",
        )

    @pytest.mark.asyncio
    async def test_cors_odpowiedz_zawiera_allow_credentials(
        self, client: AsyncClient
    ) -> None:
        """
        Odpowiedź CORS powinna zawierać nagłówek allow_credentials: true,
        bo aplikacja używa HttpOnly cookie do sesji.
        """
        response = await client.get(
            "/",
            headers={"Origin": "http://localhost:5050"},
        )

        # allow_credentials niezbędne dla cookie cross-origin
        allow_cred = response.headers.get("access-control-allow-credentials", "")
        assert allow_cred.lower() == "true"

    @pytest.mark.asyncio
    async def test_cors_drugi_dozwolony_origin(
        self, client: AsyncClient
    ) -> None:
        """
        Drugi dozwolony origin (port 8001) też powinien przechodzić przez CORS.
        """
        response = await client.options(
            "/",
            headers={
                "Origin": "http://localhost:8001",
                "Access-Control-Request-Method": "GET",
            },
        )

        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin in ("http://localhost:8001", "*")
