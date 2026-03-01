"""
Testy integracyjne — endpointy /login, /callback, /logout.

Używają httpx.AsyncClient z ASGITransport, by testować endpointy FastAPI
bezpośrednio, bez uruchamiania serwera.

Strategia mockowania:
- OIDCService jest mockowany (brak połączenia z Keycloak)
- verify_id_token jest mockowany (brak prawdziwych kluczy RSA)
- Baza danych nie jest wymagana (auth nie pisze do DB w tym etapie)

Każda klasa testowa odpowiada jednemu endpointowi.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from config import Settings

# Ustawienia testowe (bez prawdziwego .env)
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
)

# Przykładowe claims po walidacji id_token
FAKE_CLAIMS: dict[str, Any] = {
    "sub": "user-abc-123",
    "email": "test@example.com",
    "name": "Test User",
    "preferred_username": "testuser",
    "iss": TEST_SETTINGS.OIDC_ISSUER,
    "aud": TEST_SETTINGS.OIDC_CLIENT_ID,
    "exp": int(time.time()) + 3600,
}


# --------------------------------------------------------------------------- #
#  Fixture: klient HTTP do testów integracyjnych
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    Tworzy AsyncClient z transportem ASGI — testuje endpointy FastAPI
    bez uruchamiania prawdziwego serwera HTTP.

    Mockuje wszystkie zewnętrzne zależności (OIDC, DB).
    """
    # Mockujemy tworzenie tabel (nie ma prawdziwej bazy)
    with (
        patch("main.Base.metadata.create_all"),
        patch("main.get_settings", return_value=TEST_SETTINGS),
        patch("auth.router.get_settings", return_value=TEST_SETTINGS),
        patch("dependencies.get_settings", return_value=TEST_SETTINGS),
    ):
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            follow_redirects=False,  # Chcemy sprawdzać przekierowania ręcznie
        ) as ac:
            yield ac


# --------------------------------------------------------------------------- #
#  Testy: GET /login
# --------------------------------------------------------------------------- #


class TestLoginEndpoint:
    """Testy integracyjne endpointu GET /login."""

    @pytest.mark.asyncio
    async def test_login_zwraca_302(self, client: AsyncClient) -> None:
        """
        GET /login powinien zwrócić redirect 302 do OIDC providera.
        """
        # Mockujemy OIDCService.build_authorization_url (nie ma połączenia z Keycloak)
        with patch("auth.router.OIDCService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.build_authorization_url.return_value = (
                "https://keycloak.test/auth?response_type=code&state=abc123"
            )
            mock_service_cls.return_value = mock_service

            response = await client.get("/login")

        assert response.status_code == 302

    @pytest.mark.asyncio
    async def test_login_ustawia_oidc_state_cookie(
        self, client: AsyncClient
    ) -> None:
        """
        GET /login musi ustawić HttpOnly cookie 'oidc_state' z wartością state.
        To jest mechanizm CSRF protection.
        """
        with patch("auth.router.OIDCService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.build_authorization_url.return_value = (
                "https://keycloak.test/auth?state=random-state"
            )
            mock_service_cls.return_value = mock_service

            response = await client.get("/login")

        # Cookie 'oidc_state' musi być ustawiony
        assert "oidc_state" in response.cookies

    @pytest.mark.asyncio
    async def test_login_redirect_wskazuje_na_providera(
        self, client: AsyncClient
    ) -> None:
        """
        URL przekierowania z /login musi wskazywać na OIDC providera.
        """
        expected_url = "https://keycloak.test/auth?response_type=code"

        with patch("auth.router.OIDCService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.build_authorization_url.return_value = expected_url
            mock_service_cls.return_value = mock_service

            response = await client.get("/login")

        location = response.headers.get("location", "")
        assert location == expected_url


# --------------------------------------------------------------------------- #
#  Testy: GET /callback
# --------------------------------------------------------------------------- #


class TestCallbackEndpoint:
    """Testy integracyjne endpointu GET /callback."""

    @pytest.mark.asyncio
    async def test_callback_bez_code_zwraca_400(
        self, client: AsyncClient
    ) -> None:
        """
        /callback bez parametru 'code' powinien zwrócić 400 Bad Request.
        """
        response = await client.get(
            "/callback",
            params={"state": "some-state"},
            cookies={"oidc_state": "some-state"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_bez_state_zwraca_400(
        self, client: AsyncClient
    ) -> None:
        """
        /callback bez parametru 'state' powinien zwrócić 400 Bad Request.
        """
        response = await client.get(
            "/callback",
            params={"code": "some-code"},
            cookies={"oidc_state": "expected-state"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_z_blednym_state_zwraca_400(
        self, client: AsyncClient
    ) -> None:
        """
        Gdy state z URL nie zgadza się z cookie, musi być 400 (CSRF protection).
        """
        response = await client.get(
            "/callback",
            params={"code": "my-code", "state": "INNY-STATE"},
            cookies={"oidc_state": "OCZEKIWANY-STATE"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_z_error_od_providera_zwraca_400(
        self, client: AsyncClient
    ) -> None:
        """
        Gdy OIDC provider zwróci parametr 'error' (np. access_denied), powinno być 400.
        """
        response = await client.get(
            "/callback",
            params={"error": "access_denied", "state": "s"},
            cookies={"oidc_state": "s"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_sukces_ustawia_session_cookie(
        self, client: AsyncClient
    ) -> None:
        """
        Pomyślny callback (poprawny code + state) musi:
        1. Zwrócić 302 redirect na /
        2. Ustawić HttpOnly cookie 'session' z id_tokenem
        3. Usunąć tymczasowe cookie 'oidc_state'
        """
        good_state = "valid-state-for-test"
        fake_id_token = "fake.jwt.token"

        with (
            patch("auth.router.OIDCService") as mock_service_cls,
            patch("auth.router.verify_id_token", return_value=FAKE_CLAIMS),
        ):
            mock_service = AsyncMock()
            mock_service.exchange_code_for_tokens.return_value = {
                "access_token": "acc-tok",
                "id_token": fake_id_token,
                "refresh_token": "ref-tok",
            }
            mock_service.get_jwks.return_value = {"keys": []}
            mock_service_cls.return_value = mock_service

            response = await client.get(
                "/callback",
                params={"code": "good-code", "state": good_state},
                cookies={"oidc_state": good_state},
            )

        # Po pomyślnej autoryzacji — redirect na /
        assert response.status_code == 302
        assert response.headers.get("location") == "/"

        # Cookie sesji musi być ustawione
        assert "session" in response.cookies


# --------------------------------------------------------------------------- #
#  Testy: GET /logout
# --------------------------------------------------------------------------- #


class TestLogoutEndpoint:
    """Testy integracyjne endpointu GET /logout."""

    @pytest.mark.asyncio
    async def test_logout_usuwa_session_cookie(
        self, client: AsyncClient
    ) -> None:
        """
        GET /logout musi usunąć cookie 'session'.
        Sprawdzamy, że cookie ma max_age=0 lub jest nieobecne po wylogowaniu.
        """
        fake_end_session_url = "https://keycloak.test/logout?post_logout_redirect_uri=http://testserver/"

        with patch("auth.router.OIDCService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_end_session_url.return_value = fake_end_session_url
            mock_service_cls.return_value = mock_service

            response = await client.get(
                "/logout",
                cookies={"session": "fake.jwt.token"},
            )

        # Redirect do OIDC end_session_endpoint
        assert response.status_code == 302
        assert response.headers.get("location") == fake_end_session_url

        # Cookie 'session' musi być skasowane (Set-Cookie z max-age=0 lub expires w przeszłości)
        set_cookie_header = response.headers.get("set-cookie", "")
        assert "session" in set_cookie_header
        # FastAPI używa Max-Age=0 do usuwania cookies
        assert "max-age=0" in set_cookie_header.lower() or "expires" in set_cookie_header.lower()

    @pytest.mark.asyncio
    async def test_logout_bez_sesji_rowniez_przekierowuje(
        self, client: AsyncClient
    ) -> None:
        """
        /logout bez aktywnej sesji (bez cookie) też powinien przekierować.
        Wylogowanie zawsze powinno działać, nawet gdy sesja już wygasła.
        """
        with patch("auth.router.OIDCService") as mock_service_cls:
            mock_service = AsyncMock()
            mock_service.get_end_session_url.return_value = (
                "https://keycloak.test/logout"
            )
            mock_service_cls.return_value = mock_service

            response = await client.get("/logout")

        assert response.status_code == 302
