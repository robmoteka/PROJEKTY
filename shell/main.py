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
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auth import router as auth_router
from config import Settings, get_settings
from db import Base, engine
from dependencies import get_current_user
from middleware import htmx_generic_exception_handler, htmx_http_exception_handler

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

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
app.add_exception_handler(Exception, htmx_generic_exception_handler)  # type: ignore[arg-type]

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
        },
    )


@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Endpoint health check — używany przez Docker i Nginx do sprawdzania dostępności."""
    return {"status": "ok", "service": "shell"}
