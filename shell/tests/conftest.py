"""
Globalna konfiguracja pytest dla modułu shell.

Ten plik jest automatycznie ładowany przez pytest.
Zawiera konfigurację asyncio i fixtures wielokrotnego użytku:
- pytest_configure: rejestracja markera asyncio
- test_settings: ustawienia bez prawdziwego .env
- sample_claims: przykładowe claims OIDC z rolami
- client: AsyncClient z transportem ASGI do testów integracyjnych
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from config import Settings


# Konfiguracja pętli asyncio dla wszystkich testów async w tym module
def pytest_configure(config: pytest.Config) -> None:
    """Konfiguracja pytest — rejestracja markera asyncio."""
    config.addinivalue_line(
        "markers",
        "asyncio: oznacza test jako asynchroniczny (obsługiwany przez pytest-asyncio)",
    )


@pytest.fixture
def test_settings() -> Settings:
    """
    Ustawienia testowe — nie wymagają prawdziwego pliku .env.

    Używane we wszystkich testach wymagających obiektu Settings,
    bez potrzeby łączenia się z Keycloak ani PostgreSQL.
    """
    return Settings(
        OIDC_ISSUER="https://keycloak.test/realms/it-os",
        OIDC_CLIENT_ID="shell-test",
        OIDC_CLIENT_SECRET="test-secret",
        OIDC_REDIRECT_URI="http://testserver/callback",
        JWT_ALGORITHM="RS256",
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_MAX_AGE=3600,
        SECRET_KEY="test-only-secret",
        POSTGRES_HOST="localhost",
        CORS_ORIGINS="http://testserver,http://localhost:5050",
    )


@pytest.fixture
def sample_claims() -> dict[str, Any]:
    """
    Przykładowe claims z ID tokenu OIDC (z rolami).

    Zawiera wszystkie standardowe pola OIDC używane przez Shell:
    sub, email, name, preferred_username, realm_access.roles.
    """
    return {
        "sub": "user-123",
        "email": "jan@example.com",
        "name": "Jan Kowalski",
        "preferred_username": "jkowalski",
        "iss": "https://keycloak.test/realms/it-os",
        "aud": "shell-test",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "realm_access": {"roles": ["developer"]},
    }


@pytest_asyncio.fixture
async def client(test_settings: Settings) -> AsyncClient:
    """
    Klient HTTP do testów integracyjnych Shell.

    Tworzy AsyncClient z transportem ASGI — testuje endpointy FastAPI
    bez uruchamiania prawdziwego serwera HTTP. Mockuje:
    - tworzenie tabel bazy (brak połączenia z PostgreSQL)
    - get_settings — zastępuje prawdziwy .env ustawieniami testowymi

    Yields:
        Skonfigurowany AsyncClient gotowy do wysyłania żądań.
    """
    with (
        patch("main.Base.metadata.create_all"),
        patch("main.get_settings", return_value=test_settings),
        patch("auth.router.get_settings", return_value=test_settings),
        patch("dependencies.get_settings", return_value=test_settings),
    ):
        from main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            follow_redirects=False,
        ) as ac:
            yield ac
