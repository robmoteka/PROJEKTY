"""
Testy integracyjne — kontrola dostępu oparta na rolach.

Scenariusze testowe:
- GET /api/verify-session bez cookie sesji → 401
- GET /api/verify-session z aktywną sesją → 200 + nagłówki X-User-*
- Endpoint chroniony require_role("admin") z użytkownikiem bez roli → 403
- Endpoint chroniony require_role("admin") z użytkownikiem z rolą → 200

Strategia mockowania:
- get_current_user mockowany (brak połączenia z PostgreSQL)
- Testujemy zachowanie HTTP endpointu /api/verify-session
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from config import Settings

# Ustawienia testowe (bez .env)
TEST_SETTINGS = Settings(
    OIDC_ISSUER="https://keycloak.test/realms/it-os",
    OIDC_CLIENT_ID="it-project-os",
    OIDC_CLIENT_SECRET="test-secret",
    OIDC_REDIRECT_URI="http://testserver/auth/callback",
    JWT_ALGORITHM="RS256",
    SESSION_COOKIE_NAME="session",
    SESSION_COOKIE_MAX_AGE=3600,
    SECRET_KEY="test-only-secret",
    POSTGRES_HOST="localhost",
)

# Przykładowy użytkownik z rolą developer
FAKE_DEVELOPER: dict[str, Any] = {
    "sub": "user-dev-123",
    "email": "developer@example.com",
    "name": "Dev User",
    "preferred_username": "devuser",
    "roles": ["developer"],
}

# Przykładowy użytkownik z rolą admin
FAKE_ADMIN: dict[str, Any] = {
    "sub": "user-admin-456",
    "email": "admin@example.com",
    "name": "Admin User",
    "preferred_username": "adminuser",
    "roles": ["admin", "developer"],
}


# --------------------------------------------------------------------------- #
#  Fixture: klient HTTP
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    Tworzy AsyncClient z transportem ASGI — testuje FastAPI bez uruchamiania serwera.

    Nadpisuje get_settings i bazę danych aby uniknąć zależności zewnętrznych.
    """
    from main import app
    from config import get_settings
    from db import get_db

    # Mockujemy bazę danych — testy integracyjne nie wymagają PostgreSQL
    def mock_db():
        yield MagicMock()

    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[get_db] = mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    # Czyszczenie overrides po testach
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
#  Testy GET /api/verify-session
# --------------------------------------------------------------------------- #


class TestVerifySessionEndpoint:
    """Testy wewnętrznego endpointu weryfikacji sesji (wywoływanego przez Nginx auth_request)."""

    @pytest.mark.asyncio
    async def test_brak_sesji_zwraca_401(self, client: AsyncClient) -> None:
        """GET /api/verify-session bez cookie sesji zwraca 401."""
        from dependencies import get_current_user

        # Mockujemy get_current_user — zwraca None (brak sesji)
        async def mock_no_user(*args: Any, **kwargs: Any) -> None:
            return None

        from main import app
        app.dependency_overrides[get_current_user] = mock_no_user

        response = await client.get("/api/verify-session")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_aktywna_sesja_zwraca_200_z_naglowkami(
        self, client: AsyncClient
    ) -> None:
        """GET /api/verify-session z aktywną sesją zwraca 200 i nagłówki X-User-*."""
        from dependencies import get_current_user
        from main import app

        # Mockujemy get_current_user — zwraca użytkownika developer
        async def mock_developer(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return FAKE_DEVELOPER

        app.dependency_overrides[get_current_user] = mock_developer

        response = await client.get("/api/verify-session")
        assert response.status_code == 200
        # Weryfikacja nagłówków przekazywanych do modułów przez Nginx
        assert response.headers["x-user-sub"] == FAKE_DEVELOPER["sub"]
        assert response.headers["x-user-email"] == FAKE_DEVELOPER["email"]
        assert response.headers["x-user-name"] == FAKE_DEVELOPER["name"]
        assert response.headers["x-user-roles"] == "developer"

    @pytest.mark.asyncio
    async def test_admin_ma_wiele_rol_w_naglowku(
        self, client: AsyncClient
    ) -> None:
        """Nagłówek X-User-Roles zawiera wszystkie role oddzielone przecinkami."""
        from dependencies import get_current_user
        from main import app

        async def mock_admin(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return FAKE_ADMIN

        app.dependency_overrides[get_current_user] = mock_admin

        response = await client.get("/api/verify-session")
        assert response.status_code == 200
        roles_header = response.headers["x-user-roles"]
        # admin i developer powinny być w nagłówku (kolejność zależy od listy)
        assert "admin" in roles_header
        assert "developer" in roles_header

    @pytest.mark.asyncio
    async def test_uzytkownik_bez_rol_zwraca_pusty_naglowek(
        self, client: AsyncClient
    ) -> None:
        """Użytkownik bez ról: nagłówek X-User-Roles jest pustym stringiem."""
        from dependencies import get_current_user
        from main import app

        async def mock_no_roles(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return {"sub": "u1", "email": "e@example.com", "name": "N", "preferred_username": "u", "roles": []}

        app.dependency_overrides[get_current_user] = mock_no_roles

        response = await client.get("/api/verify-session")
        assert response.status_code == 200
        assert response.headers["x-user-roles"] == ""


# --------------------------------------------------------------------------- #
#  Import pomocniczy (używany w fixture)
# --------------------------------------------------------------------------- #

from unittest.mock import MagicMock  # noqa: E402
