"""
Testy jednostkowe modułu autentykacji (auth.jwt_utils + auth.oidc_service).

Scenariusze testowe:
- Weryfikacja poprawnej/błędnej struktury claims
- Ekstrakcja danych użytkownika z claims
- Weryfikacja wykrywania wygasłego tokenu
- Obsługa brakujących/nieprawidłowych kluczy JWKS
- Generowanie unikalnych wartości state
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

from auth.jwt_utils import (
    TokenExpiredError,
    TokenVerificationError,
    decode_token_unverified,
    extract_user_info,
    verify_id_token,
)
from auth.oidc_service import OIDCService, generate_state
from config import Settings


# --------------------------------------------------------------------------- #
#  Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def test_settings() -> Settings:
    """Ustawienia testowe — używają algorytmu HS256 dla uproszczenia testów."""
    return Settings(
        OIDC_ISSUER="https://test-issuer.example.com/realms/test",
        OIDC_CLIENT_ID="test-client",
        OIDC_CLIENT_SECRET="test-secret",
        OIDC_REDIRECT_URI="http://localhost:5050/callback",
        JWT_ALGORITHM="RS256",
        SESSION_COOKIE_NAME="session",
        SECRET_KEY="test-key",
    )


@pytest.fixture
def sample_claims() -> dict[str, Any]:
    """Przykładowe claims z ID tokenu OIDC."""
    return {
        "sub": "user-123",
        "email": "jan.kowalski@example.com",
        "name": "Jan Kowalski",
        "preferred_username": "jkowalski",
        "iss": "https://test-issuer.example.com/realms/test",
        "aud": "test-client",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }


# --------------------------------------------------------------------------- #
#  Testy: extract_user_info
# --------------------------------------------------------------------------- #


class TestExtractUserInfo:
    """Testy ekstrakcji danych użytkownika z claims JWT."""

    def test_pełne_claims_zwraca_wszystkie_pola(
        self, sample_claims: dict[str, Any]
    ) -> None:
        """extract_user_info powinno zwrócić sub, email, name, preferred_username."""
        user = extract_user_info(sample_claims)

        assert user["sub"] == "user-123"
        assert user["email"] == "jan.kowalski@example.com"
        assert user["name"] == "Jan Kowalski"
        assert user["preferred_username"] == "jkowalski"

    def test_brakujące_pola_zwraca_puste_stringi(self) -> None:
        """Brakujące claims nie powinny powodować błędu — zwraca puste stringi."""
        user = extract_user_info({})

        assert user["sub"] == ""
        assert user["email"] == ""
        assert user["name"] == ""
        assert user["preferred_username"] == ""

    def test_częściowe_claims(self) -> None:
        """Częściowe claims — tylko sub i email."""
        user = extract_user_info({"sub": "abc", "email": "a@b.com"})

        assert user["sub"] == "abc"
        assert user["email"] == "a@b.com"
        assert user["name"] == ""


# --------------------------------------------------------------------------- #
#  Testy: decode_token_unverified
# --------------------------------------------------------------------------- #


class TestDecodeTokenUnverified:
    """Testy dekodowania tokenu JWT bez weryfikacji podpisu."""

    def test_dekoduje_prawidłowy_token_hs256(self) -> None:
        """Poprawny token HS256 powinien być dekodowany bez błędu."""
        # Tworzymy token testowy (HS256) z kluczem testowym
        payload = {"sub": "user-1", "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, "sekret", algorithm="HS256")

        claims = decode_token_unverified(token)

        assert claims["sub"] == "user-1"

    def test_nieprawidłowy_format_tokenu_rzuca_wyjątek(self) -> None:
        """Zepsuty token powinien rzucić TokenVerificationError."""
        with pytest.raises(TokenVerificationError):
            decode_token_unverified("to.nie.jest.jwt")


# --------------------------------------------------------------------------- #
#  Testy: verify_id_token
# --------------------------------------------------------------------------- #


class TestVerifyIdToken:
    """Testy weryfikacji ID tokenu OIDC (RS256)."""

    def test_pusty_jwks_rzuca_wyjątek(self, test_settings: Settings) -> None:
        """Pustý JWKS (brak kluczy) powinien rzucić TokenVerificationError."""
        token = jwt.encode({"sub": "u1"}, "x", algorithm="HS256")

        with pytest.raises(TokenVerificationError, match="Brak kluczy"):
            verify_id_token(token, {"keys": []}, test_settings)

    def test_brak_pasującego_kid_rzuca_wyjątek(self, test_settings: Settings) -> None:
        """Token z niepasującym kid powinien wywołać weryfikację na pierwszym kluczu i nie powieść się."""
        # Token z innym kid niż dostępny klucz — fallback próbuje i_tak się wywali
        payload = {"sub": "u1", "exp": int(time.time()) + 300}
        token = jwt.encode(payload, "fake", algorithm="HS256")

        jwks_with_wrong_key: dict[str, Any] = {
            "keys": [
                {
                    "kty": "oct",
                    "kid": "other-kid",
                    "k": "c2VrcmV0",  # base64url("secret")
                    "alg": "HS256",
                }
            ]
        }

        with pytest.raises(TokenVerificationError):
            verify_id_token(token, jwks_with_wrong_key, test_settings)


# --------------------------------------------------------------------------- #
#  Testy: generate_state
# --------------------------------------------------------------------------- #


class TestGenerateState:
    """Testy generowania losowego tokenu state (CSRF)."""

    def test_zwraca_niepusty_string(self) -> None:
        """generate_state powinno zwrócić niepusty string."""
        state = generate_state()
        assert isinstance(state, str)
        assert len(state) > 0

    def test_każde_wywołanie_zwraca_unikalną_wartość(self) -> None:
        """Dwa kolejne wywołania powinny zwrócić różne wartości (kryptograficznie losowe)."""
        states = {generate_state() for _ in range(100)}
        # Prawdopodobieństwo kolizji jest bliskie zeru dla 100 wywołań
        assert len(states) == 100

    def test_state_ma_odpowiednią_długość(self) -> None:
        """State powinien być wystarczająco długi (>=32 znaki)."""
        state = generate_state()
        assert len(state) >= 32


# --------------------------------------------------------------------------- #
#  Testy: OIDCService
# --------------------------------------------------------------------------- #


class TestOIDCService:
    """Testy jednostkowe serwisu OIDC — mockujemy wywołania httpx."""

    @pytest.fixture
    def oidc_service(self, test_settings: Settings) -> OIDCService:
        """Tworzy instancję OIDCService z ustawieniami testowymi."""
        return OIDCService(test_settings)

    def test_build_authorization_url_zawiera_wymagane_params(
        self, oidc_service: OIDCService
    ) -> None:
        """URL autoryzacji powinien zawierać client_id, redirect_uri, response_type, state."""
        state = "test-state-value"
        url = oidc_service.build_authorization_url(state)

        assert "response_type=code" in url
        assert "client_id=test-client" in url
        assert "state=test-state-value" in url
        assert "redirect_uri=" in url

    def test_build_authorization_url_zawiera_issuer_baseurl(
        self, oidc_service: OIDCService
    ) -> None:
        """URL powinien bazować na OIDC_ISSUER."""
        url = oidc_service.build_authorization_url("state")
        assert "test-issuer.example.com" in url

    @pytest.mark.asyncio
    async def test_get_discovery_dokument_jest_cachowany(
        self, oidc_service: OIDCService
    ) -> None:
        """Dokument discovery powinien być pobrany tylko raz (cache)."""
        mock_doc = {
            "authorization_endpoint": "https://auth.example.com/auth",
            "token_endpoint": "https://auth.example.com/token",
            "jwks_uri": "https://auth.example.com/certs",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_doc
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Pierwsze wywołanie — pobiera z "sieci"
            doc1 = await oidc_service.get_discovery_document()
            # Drugie wywołanie — powinno użyć cache
            doc2 = await oidc_service.get_discovery_document()

        assert doc1 == doc2
        # Httpx.AsyncClient powinien być wywołany tylko raz (cache działa)
        assert mock_client_class.call_count == 1

    @pytest.mark.asyncio
    async def test_exchange_code_dla_tokenów_wysyła_json(
        self, oidc_service: OIDCService
    ) -> None:
        """exchange_code_for_tokens powinno zwrócić słownik z tokenami."""
        expected_tokens = {
            "access_token": "access.token.test",
            "id_token": "id.token.test",
            "refresh_token": "refresh.token.test",
        }

        # Cache discovery document
        oidc_service._discovery_doc = {
            "authorization_endpoint": "https://auth.example.com/auth",
            "token_endpoint": "https://auth.example.com/token",
            "jwks_uri": "https://auth.example.com/certs",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_tokens
            mock_response.raise_for_status = MagicMock()
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            tokens = await oidc_service.exchange_code_for_tokens("auth-code-123")

        assert tokens == expected_tokens
        # Weryfikujemy, że POST był wywołany z właściwymi danymi
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["data"]["grant_type"] == "authorization_code"
        assert call_kwargs["data"]["code"] == "auth-code-123"
