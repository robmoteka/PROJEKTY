"""
Główna aplikacja Shell — punkt wejścia FastAPI.

Shell pełni rolę orkiestratora mikrofrontendów HTMX:
- Serwuje główny layout HTML (base.html) z nawigacją
- Dostarcza endpointy autentykacji OIDC (/login, /callback, /logout)
- Rejestruje routery modułów i eksponuje je jako partiale HTMX
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from auth import router as auth_router
from config import Settings, get_settings
from db import Base, engine
from dependencies import get_current_user, require_authenticated_user
from middleware import htmx_http_exception_handler

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

SUPPORTED_MODULES: set[str] = {"issues", "projekty"}

# --------------------------------------------------------------------------- #
#  Inicjalizacja aplikacji
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="IT Project OS — Shell",
    description="Mikrofrontend Shell: layout, nawigacja, autentykacja OIDC.",
    version="1.0.0",
)

# --------------------------------------------------------------------------- #
#  Rejestracja middleware (kolejność ma znaczenie: CORS przed routerami)
# --------------------------------------------------------------------------- #

# CORS — dozwolone origins dla środowiska deweloperskiego
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Globalne handlery błędów — HTMX otrzymuje HTML partial, REST otrzymuje JSON
app.add_exception_handler(HTTPException, htmx_http_exception_handler)  # type: ignore[arg-type]

# Tworzenie tabel przy starcie (w produkcji używaj Alembic)
@app.on_event("startup")
async def startup() -> None:
    """Inicjalizacja bazy danych przy starcie aplikacji."""
    Base.metadata.create_all(bind=engine)
    logger.info("Baza danych zainicjalizowana.")


# Szablony Jinja2
templates = Jinja2Templates(directory="templates")

# --------------------------------------------------------------------------- #
#  Rejestracja routerów
# --------------------------------------------------------------------------- #

# Router autentykacji OIDC (endpointy: /login, /callback, /logout)
app.include_router(auth_router)

# --------------------------------------------------------------------------- #
#  Strona główna
# --------------------------------------------------------------------------- #


@app.get("/", response_class=HTMLResponse, summary="Strona główna (pełny layout)")
async def index(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[dict | None, Depends(get_current_user)],
) -> HTMLResponse:
    """
    Renderuje pełny layout HTML z nawigacją i główną treścią.

    Strona główna otacza całą aplikację — moduły ładowane są przez
    HTMX (hx-get) do elementu #main-content bez przeładowania strony.

    Args:
        request: Obiekt żądania FastAPI (wymagany przez Jinja2).
        current_user: Dane zalogowanego użytkownika lub None.

    Returns:
        Pełna strona HTML z layoutem aplikacji.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": current_user,
            "app_title": "IT Project OS",
            "initial_module_url": None,
        },
    )


@app.get(
    "/modules/{module_name}/",
    response_class=HTMLResponse,
    summary="Fallback pełnego layoutu dla URL modułu",
)
@app.get(
    "/modules/{module_name}/{module_path:path}",
    response_class=HTMLResponse,
    summary="Fallback pełnego layoutu dla zagnieżdżonych URL modułu",
)
async def module_entrypoint(
    request: Request,
    module_name: str,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[dict | None, Depends(get_current_user)],
    module_path: str = "",
) -> HTMLResponse:
    """
    Renderuje pełny layout Shell dla bezpośredniego wejścia na adres modułu.

    Ten endpoint jest używany przy pełnym przeładowaniu strony pod adresem
    `/modules/<name>/...` (bez nagłówka `HX-Request`). Shell renderuje wtedy
    pełny layout i automatycznie dociąga właściwy partial modułu przez HTMX
    do `#main-content`.

    Args:
        request: Obiekt żądania FastAPI (wymagany przez Jinja2).
        module_name: Nazwa modułu z URL (np. issues, projekty).
        current_user: Dane zalogowanego użytkownika lub None.
        module_path: Opcjonalna zagnieżdżona ścieżka modułu.

    Returns:
        Pełna strona HTML Shell z automatycznym bootstrapem HTMX.

    Raises:
        HTTPException: Gdy moduł nie znajduje się na liście obsługiwanych.
    """
    if module_name not in SUPPORTED_MODULES:
        raise HTTPException(status_code=404, detail="Nieznany moduł.")

    initial_module_url = request.url.path
    if request.url.query:
        initial_module_url = f"{initial_module_url}?{request.url.query}"

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": current_user,
            "app_title": "IT Project OS",
            "initial_module_url": initial_module_url,
        },
    )


@app.get("/profile", response_class=HTMLResponse, summary="Strona profilu użytkownika")
async def profile(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    current_user: Annotated[dict, Depends(require_authenticated_user)],
) -> HTMLResponse:
    """
    Renderuje stronę profilu zalogowanego użytkownika.

    Wyświetla dane z sesji OIDC (read-only) oraz link do panelu konta
    Keycloak umożliwiającego zmianę hasła.

    Args:
        request: Obiekt żądania FastAPI (wymagany przez Jinja2).
        current_user: Dane zalogowanego użytkownika (wymaga sesji — 401 jeśli brak).

    Returns:
        Pełna strona HTML z profilem użytkownika.
    """
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "keycloak_account_url": settings.KEYCLOAK_ACCOUNT_URL,
        },
    )


@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Endpoint health check — używany przez Docker i Nginx do sprawdzania dostępności."""
    return {"status": "ok", "service": "shell"}


@app.get("/api/verify-session", summary="Wewnętrzna weryfikacja sesji (Nginx auth_request)")
async def verify_session(
    current_user: Annotated[dict | None, Depends(get_current_user)],
    response: Response,
) -> Response:
    """
    Endpoint weryfikacji sesji użytkownika — wywoływany przez Nginx auth_request.

    Nginx wywołuje ten endpoint przed każdym request do modułów. Jeśli sesja
    jest aktywna, zwraca 200 i nagłówki X-User-* przekazywane dalej do modułu.
    Jeśli brak sesji, zwraca 401 — Nginx blokuje request i przekierowuje na /login.

    Args:
        current_user: Dane zalogowanego użytkownika (None = niezalogowany).
        response: Obiekt odpowiedzi FastAPI — używany do ustawiania nagłówków.

    Returns:
        200 z nagłówkami X-User-* lub 401 brak autoryzacji.
    """
    # Brak sesji — 401 powoduje blokadę request przez Nginx
    if not current_user:
        raise HTTPException(status_code=401, detail="Brak aktywnej sesji.")

    # Przekazujemy dane użytkownika jako nagłówki do modułu
    response.headers["X-User-Sub"] = current_user.get("sub", "")
    response.headers["X-User-Email"] = current_user.get("email", "")
    response.headers["X-User-Name"] = current_user.get("name", "")
    # Role jako lista rozdzielona przecinkami (np. "developer,viewer")
    roles: list[str] = current_user.get("roles", [])
    response.headers["X-User-Roles"] = ",".join(roles)
    return Response(status_code=200)
