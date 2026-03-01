"""
Serwis OIDC — komunikacja z providerem tożsamości (Keycloak / Azure AD).

Odpowiedzialności:
- Pobieranie dokumentu odkrywczego (/.well-known/openid-configuration)
- Budowanie URL autoryzacji (krok 1 flow Authorization Code)
- Wymiana kodu autoryzacyjnego na tokeny (krok 3)
- Pobieranie JWKS (kluczy publicznych) do weryfikacji tokenów
"""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

from config import Settings


class OIDCDiscoveryError(Exception):
    """Błąd podczas pobierania danych discovery/JWKS z providera OIDC."""


class OIDCTokenError(Exception):
    """Błąd podczas wymiany kodu autoryzacyjnego na tokeny OIDC."""


class OIDCService:
    """Obsługuje komunikację z providerem OIDC zgodnie ze specyfikacją OpenID Connect."""

    def __init__(self, settings: Settings) -> None:
        """Inicjalizuje serwis ustawieniami aplikacji."""
        self._settings = settings
        self._discovery_doc: dict[str, Any] | None = None

    async def get_discovery_document(self) -> dict[str, Any]:
        """
        Pobiera i cachuje dokument OpenID Connect Discovery.

        Returns:
            Słownik metadanych providera OIDC.

        Raises:
            OIDCDiscoveryError: Gdy request do endpointu discovery nie powiedzie się.
        """
        if self._discovery_doc is None:
            discovery_url = (
                f"{self._settings.OIDC_ISSUER}/.well-known/openid-configuration"
            )
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(discovery_url, timeout=10.0)
                    response.raise_for_status()
                except httpx.HTTPError as exc:
                    raise OIDCDiscoveryError(
                        f"Nie można pobrać dokumentu discovery z {discovery_url}: {exc}"
                    ) from exc
                self._discovery_doc = response.json()
        if self._discovery_doc is None:
            raise OIDCDiscoveryError("Dokument discovery OIDC jest niedostępny.")
        return self._discovery_doc

    def build_authorization_url(self, state: str) -> str:
        """
        Buduje URL do przekierowania użytkownika na stronę logowania providera.

        Args:
            state: Losowy token CSRF zapobiegający atakom CSRF.

        Returns:
            Pełny URL autoryzacji z parametrami query.
        """
        params = {
            "response_type": "code",
            "client_id": self._settings.OIDC_CLIENT_ID,
            "redirect_uri": self._settings.OIDC_REDIRECT_URI,
            "scope": self._settings.OIDC_SCOPES,
            "state": state,
        }
        auth_endpoint = (
            f"{self._settings.OIDC_ISSUER}/protocol/openid-connect/auth"
        )
        return f"{auth_endpoint}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        """
        Wymienia kod autoryzacyjny na zestaw tokenów (krok 3 flow OIDC).

        Args:
            code: Kod autoryzacyjny otrzymany w callbacku od providera.

        Returns:
            Słownik z tokenami: access_token, id_token, refresh_token, expires_in.

        Raises:
            OIDCTokenError: Gdy provider zwróci błąd lub request się nie powiedzie.
        """
        doc = await self.get_discovery_document()
        token_endpoint: str = doc["token_endpoint"]

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._settings.OIDC_REDIRECT_URI,
            "client_id": self._settings.OIDC_CLIENT_ID,
            "client_secret": self._settings.OIDC_CLIENT_SECRET,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    token_endpoint,
                    data=payload,
                    timeout=15.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise OIDCTokenError(
                    f"Błąd wymiany kodu na tokeny ({token_endpoint}): {exc}"
                ) from exc

        return response.json()

    async def get_jwks(self) -> dict[str, Any]:
        """
        Pobiera JWKS (JSON Web Key Set) — klucze publiczne do weryfikacji tokenów.

        Returns:
            Słownik JWKS z kluczami publicznymi.

        Raises:
            OIDCDiscoveryError: Gdy nie uda się pobrać discovery lub JWKS.
        """
        doc = await self.get_discovery_document()
        jwks_uri: str = doc["jwks_uri"]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(jwks_uri, timeout=10.0)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise OIDCDiscoveryError(
                    f"Błąd pobierania JWKS z {jwks_uri}: {exc}"
                ) from exc

        return response.json()

    async def get_end_session_url(self, id_token_hint: str | None = None) -> str:
        """
        Zwraca URL wylogowania po stronie OIDC providera.

        Args:
            id_token_hint: Opcjonalny id_token przekazany jako hint do providera.

        Returns:
            URL do przekierowania po wylogowaniu.
        """
        doc = await self.get_discovery_document()
        end_session_endpoint: str = doc.get(
            "end_session_endpoint",
            f"{self._settings.OIDC_ISSUER}/protocol/openid-connect/logout",
        )
        params: dict[str, str] = {
            "post_logout_redirect_uri": self._settings.OIDC_REDIRECT_URI.replace(
                "/callback", "/"
            ),
        }
        if id_token_hint:
            params["id_token_hint"] = id_token_hint

        return f"{end_session_endpoint}?{urlencode(params)}"


def generate_state() -> str:
    """Generuje kryptograficznie bezpieczny losowy token stanu (CSRF protection)."""
    return secrets.token_urlsafe(32)
