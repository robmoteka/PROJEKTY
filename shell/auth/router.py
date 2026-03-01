"""
Router autentykacji — endpointy OIDC Authorization Code Flow.

Endpointy:
- GET /login      — inicjuje logowanie (redirect do OIDC providera)
- GET /callback   — obsługuje odpowiedź providera (wymiana kodu, zapis sesji)
- GET /logout     — wylogowanie (czyszczenie sesji + redirect do providera)

Wzorzec BFF (Backend For Frontend):
Tokeny JWT są przechowywane wyłącznie po stronie serwera lub w HttpOnly cookie.
Frontend NIGDY nie widzi surowych tokenów.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth.jwt_utils import (
    TokenVerificationError,
    extract_user_info,
    verify_id_token,
)
from auth.oidc_service import OIDCService, generate_state
from config import Settings, get_settings
from db import get_db
from models import UserSession

# Logger dla modułu autentykacji
logger = logging.getLogger(__name__)

# Router dla ścieżek /login, /callback, /logout
router = APIRouter(tags=["auth"])

# --------------------------------------------------------------------------- #
#  Dependency — serwis OIDC (singleton przez czas życia requesta)
# --------------------------------------------------------------------------- #


def get_oidc_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OIDCService:
    """Tworzy instancję OIDCService — wstrzykiwana przez FastAPI DI."""
    return OIDCService(settings)


# --------------------------------------------------------------------------- #
#  GET /login
# --------------------------------------------------------------------------- #


@router.get("/login", summary="Inicjuje przepływ logowania OIDC")
async def login(
    settings: Annotated[Settings, Depends(get_settings)],
    oidc: Annotated[OIDCService, Depends(get_oidc_service)],
) -> RedirectResponse:
    """
    Krok 1 — przekierowanie użytkownika do providera OIDC.

    Generuje losowy state (CSRF token) i zapisuje go w krótkotrwałym
    HttpOnly cookie 'oidc_state'. Następnie przekierowuje przeglądarkę
    na stronę logowania (authorization_endpoint providera).

    Returns:
        Odpowiedź 302 przekierowująca do OIDC authorization_endpoint.
    """
    # Generujemy nowy state przy każdym żądaniu logowania
    state = generate_state()
    # Budujemy URL do providera (synchronicznie — endpoint znamy z konfiguracji)
    authorization_url = oidc.build_authorization_url(state)

    logger.info("Inicjuję logowanie OIDC — przekierowanie do providera.")

    # Tworzymy odpowiedź z przekierowaniem
    response = RedirectResponse(url=authorization_url, status_code=302)

    # State zapisujemy w HttpOnly cookie — nie jest dostępny z JS (XSS protection)
    response.set_cookie(
        key="oidc_state",
        value=state,
        httponly=True,       # Niedostępny dla JavaScript
        secure=False,        # True w produkcji (HTTPS)!
        samesite="lax",      # Chroni przed CSRF przy GET redirectach
        max_age=300,         # State ważny 5 minut (czas na zalogowanie)
    )
    return response


# --------------------------------------------------------------------------- #
#  GET /callback
# --------------------------------------------------------------------------- #


@router.get("/callback", summary="Obsługuje callback OIDC po zalogowaniu")
async def callback(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    oidc: Annotated[OIDCService, Depends(get_oidc_service)],
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oidc_state: Annotated[str | None, Cookie()] = None,
) -> RedirectResponse:
    """
    Krok 3 — obsługa przekierowania powrotnego od OIDC providera.

    Przepływ:
    1. Weryfikuje parametr 'state' z URL względem cookie 'oidc_state' (anty-CSRF).
    2. Wymienia 'code' na tokeny (access_token, id_token, refresh_token).
    3. Weryfikuje podpis i claims ID tokenu (JWT, RS256 lub HS256).
    4. Tworzy rekord UserSession w PostgreSQL (sesja server-side).
    5. Zapisuje losowy session_id (NIE id_token) w HttpOnly cookie (wzorzec BFF).
    6. Przekierowuje użytkownika na stronę główną.

    Args:
        code: Kod autoryzacyjny od providera (parametr URL).
        state: Token CSRF od providera (parametr URL).
        error: Ewentualny błąd od providera (np. 'access_denied').
        oidc_state: Cookie z state zapisanym podczas /login.
        db: Sesja bazy danych (wstrzykiwana przez FastAPI DI).

    Returns:
        Odpowiedź 302 przekierowująca na / po pomyślnym logowaniu.

    Raises:
        HTTPException 400: Nieprawidłowy state (możliwy atak CSRF).
        HTTPException 502: Błąd przy wymianie tokenów z providerem.
        HTTPException 401: Nieprawidłowy lub wygasły id_token.
    """
    # --- Obsługa błędu od providera ---
    if error:
        logger.warning("Provider OIDC zwrócił błąd: %s", error)
        raise HTTPException(
            status_code=400,
            detail=f"Błąd logowania od providera OIDC: {error}",
        )

    # --- Walidacja obecności wymaganych parametrów ---
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Brak parametrów 'code' lub 'state' w odpowiedzi OIDC.",
        )

    # --- Weryfikacja CSRF: state z URL musi zgadzać się z cookie ---
    if not oidc_state or state != oidc_state:
        logger.warning(
            "Niezgodność CSRF state! URL state=%s, cookie state=%s",
            state,
            oidc_state,
        )
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowy token CSRF (state mismatch). Spróbuj zalogować się ponownie.",
        )

    # --- Wymiana kodu autoryzacyjnego na tokeny ---
    try:
        tokens = await oidc.exchange_code_for_tokens(code)
    except Exception as exc:
        logger.error("Błąd wymiany kodu OIDC na tokeny: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Nie można wymienić kodu na tokeny. Spróbuj ponownie.",
        ) from exc

    id_token: str = tokens.get("id_token", "")

    # --- Weryfikacja ID tokenu (JWT) ---
    try:
        jwks = await oidc.get_jwks()
        claims = verify_id_token(id_token, jwks, settings)
        user_info = extract_user_info(claims)
        logger.info(
            "Użytkownik zalogowany: sub=%s, email=%s",
            user_info["sub"],
            user_info["email"],
        )
    except TokenVerificationError as exc:
        logger.error("Nieprawidłowy ID token: %s", exc)
        raise HTTPException(
            status_code=401,
            detail=f"Nieprawidłowy token: {exc}",
        ) from exc

    # --- Zapis sesji server-side w PostgreSQL (wzorzec BFF) ---
    # Generujemy kryptograficznie bezpieczny, losowy identyfikator sesji
    session_id: str = secrets.token_urlsafe(64)

    # Obliczamy czas wygaśnięcia sesji na podstawie ustawienia SESSION_COOKIE_MAX_AGE
    expires_at: datetime = datetime.now(timezone.utc) + timedelta(
        seconds=settings.SESSION_COOKIE_MAX_AGE
    )

    # Tworzymy rekord sesji w bazie — id_token przechowujemy jako hint do wylogowania
    db_session = UserSession(
        session_id=session_id,
        user_id=user_info["sub"],
        email=user_info.get("email"),
        name=user_info.get("name"),
        preferred_username=user_info.get("preferred_username"),
        id_token=id_token,
        expires_at=expires_at,
    )
    db.add(db_session)
    db.commit()

    logger.info(
        "Sesja utworzona w DB: session_id=...(ukryty), user_id=%s, expires_at=%s",
        user_info["sub"],
        expires_at,
    )

    # --- Zapis session_id w HttpOnly cookie (NIE id_token!) ---
    # Cookie zawiera tylko opakę identyfikatora — dane są bezpiecznie w PostgreSQL
    response = RedirectResponse(url="/", status_code=302)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,                            # Niedostępny dla JS — ochrona XSS
        secure=False,                             # True w produkcji (HTTPS)!
        samesite="lax",
        max_age=settings.SESSION_COOKIE_MAX_AGE,  # Np. 3600 sekund
    )

    # Usuwamy tymczasowe cookie z state (już niepotrzebne)
    response.delete_cookie("oidc_state")

    return response


# --------------------------------------------------------------------------- #
#  GET /logout
# --------------------------------------------------------------------------- #


@router.get("/logout", summary="Wylogowanie użytkownika")
async def logout(
    settings: Annotated[Settings, Depends(get_settings)],
    oidc: Annotated[OIDCService, Depends(get_oidc_service)],
    db: Annotated[Session, Depends(get_db)],
    session: Annotated[str | None, Cookie()] = None,
) -> RedirectResponse:
    """
    Wylogowuje użytkownika lokalnie i przekierowuje do OIDC end_session_endpoint.

    Przepływ:
    1. Wyszukuje rekord UserSession po session_id z cookie.
    2. Odczytuje id_token z rekordu DB (jako id_token_hint dla providera OIDC).
    3. Usuwa rekord sesji z PostgreSQL.
    4. Usuwa cookie sesji.
    5. Przekierowuje przeglądarkę do OIDC end_session_endpoint.

    Args:
        session: Cookie z session_id (wstrzykiwane automatycznie przez FastAPI).
        db: Sesja bazy danych (wstrzykiwana przez FastAPI DI).

    Returns:
        Odpowiedź 302 przekierowująca do OIDC end_session_endpoint lub na /.
    """
    # Szukamy rekordu sesji w bazie danych na podstawie wartości cookie
    id_token_hint: str | None = None
    if session:
        db_session = (
            db.query(UserSession)
            .filter(UserSession.session_id == session)
            .first()
        )
        if db_session:
            # Odczytujemy id_token_hint przed usunięciem rekordu
            id_token_hint = db_session.id_token
            logger.info(
                "Wylogowanie użytkownika user_id=%s", db_session.user_id
            )
            # Usuwamy rekord sesji z bazy — sesja jest natychmiast unieważniona
            db.delete(db_session)
            db.commit()
        else:
            # Cookie istnieje, ale nie ma odpowiadającego rekordu w DB
            logger.warning("Wylogowanie: nie znaleziono sesji w DB dla podanego cookie.")

    # Pobieramy URL wylogowania z OIDC providera (z opcjonalnym id_token_hint)
    end_session_url = await oidc.get_end_session_url(id_token_hint=id_token_hint)

    # Tworzymy odpowiedź z przekierowaniem do providera
    response = RedirectResponse(url=end_session_url, status_code=302)

    # Usuwamy cookie sesji — to kluczowe dla bezpieczeństwa (BFF pattern)
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        secure=False,   # True w produkcji (HTTPS)!
        samesite="lax",
    )

    return response
