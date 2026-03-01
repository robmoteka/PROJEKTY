"""
Narzędzia do obsługi JWT w aplikacji Shell.

Odpowiedzialności:
- Weryfikacja podpisu ID tokenu OIDC (RS256) przy użyciu JWKS providera
- Dekodowanie ładunku tokenu (claims) bez weryfikacji (do odczytu danych po walidacji)
"""

from __future__ import annotations

from typing import Any

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from config import Settings


class TokenVerificationError(Exception):
    """Wyjątek rzucany gdy weryfikacja JWT się nie powiedzie."""


class TokenExpiredError(TokenVerificationError):
    """Wyjątek rzucany gdy token jest ważny, ale wygasł."""


def verify_id_token(
    id_token: str,
    jwks: dict[str, Any],
    settings: Settings,
) -> dict[str, Any]:
    """
    Weryfikuje podpis i claims ID tokenu OIDC.

    Waliduje:
    - Podpis kryptograficzny przy użyciu JWKS providera
    - Pole `iss` (issuer)
    - Pole `aud` (audience)
    - Pole `exp` (expiration)

    Args:
        id_token: Zakodowany JWT jako string.
        jwks: Klucze publiczne providera (JSON Web Key Set).
        settings: Ustawienia aplikacji z konfiguracją OIDC.

    Returns:
        Słownik z claims po pomyślnej weryfikacji.

    Raises:
        TokenExpiredError: Gdy token jest przeterminowany.
        TokenVerificationError: Gdy podpis lub claims są nieprawidłowe.
    """
    try:
        unverified_header = jwt.get_unverified_header(id_token)
        kid: str | None = unverified_header.get("kid")
        algorithm: str = unverified_header.get("alg", settings.JWT_ALGORITHM)

        candidate_key: dict[str, Any] | None = None
        for key_data in jwks.get("keys", []):
            if key_data.get("kid") == kid:
                candidate_key = key_data
                break

        if candidate_key is None:
            keys = jwks.get("keys", [])
            if not keys:
                raise TokenVerificationError("Brak kluczy publicznych w JWKS.")
            candidate_key = keys[0]

        if candidate_key is None:
            raise TokenVerificationError("Nie znaleziono klucza do weryfikacji JWT.")

        claims: dict[str, Any] = jwt.decode(
            id_token,
            candidate_key,
            algorithms=[algorithm],
            audience=settings.OIDC_CLIENT_ID,
            issuer=settings.OIDC_ISSUER,
            options={"verify_at_hash": False},
        )
        return claims

    except ExpiredSignatureError as exc:
        raise TokenExpiredError("ID token wygasł.") from exc
    except JWTError as exc:
        raise TokenVerificationError(f"Nieprawidłowy ID token: {exc}") from exc


def decode_token_unverified(token: str) -> dict[str, Any]:
    """
    Dekoduje payload JWT bez weryfikacji podpisu.

    Args:
        token: Zakodowany JWT jako string.

    Returns:
        Słownik claims z payload tokenu.

    Raises:
        TokenVerificationError: Gdy token ma nieprawidłowy format.
    """
    try:
        return jwt.get_unverified_claims(token)
    except JWTError as exc:
        raise TokenVerificationError(f"Nie można zdekodować tokenu: {exc}") from exc


def extract_user_info(id_token_claims: dict[str, Any]) -> dict[str, Any]:
    """
    Wyciąga podstawowe informacje o użytkowniku z claims ID tokenu.

    Obsługuje dwa schematy mapowania ról Keycloak:
    - Custom claim `roles` (ustawiany przez realm-roles-mapper w kliencie)
    - Standardowe `realm_access.roles` (domyślny format Keycloak)

    Args:
        id_token_claims: Słownik claims z zweryfikowanego ID tokenu.

    Returns:
        Słownik z kluczami: sub, email, name, preferred_username, roles.
    """
    # Próbujemy najpierw custom claim `roles` (z realm-roles-mapper)
    roles: list[str] = id_token_claims.get("roles", [])
    if not roles:
        # Fallback: standardowy format Keycloak realm_access.roles
        realm_access: dict[str, Any] = id_token_claims.get("realm_access", {})
        roles = realm_access.get("roles", [])

    return {
        "sub": id_token_claims.get("sub", ""),
        "email": id_token_claims.get("email", ""),
        "name": id_token_claims.get("name", ""),
        "preferred_username": id_token_claims.get("preferred_username", ""),
        "roles": roles,
    }
