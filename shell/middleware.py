"""
Middleware i globalne handlery wyjątków aplikacji Shell.

Zapewnia spójne odpowiedzi na błędy:
- Dla requestów HTMX (nagłówek HX-Request: true) → HTML partial z komunikatem DaisyUI
- Dla zwykłych requestów (REST/przeglądarka) → odpowiedź JSON FastAPI
- Catch-all handler loguje pełny traceback i zwraca status 500

Opcjonalnie: middleware CSRF weryfikujący tokeny dla metod mutujących.
"""

from __future__ import annotations

import logging
import traceback
from typing import Callable

from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Logger modułu middleware
logger = logging.getLogger(__name__)

# Szablony Jinja2 — ten sam katalog co w main.py
templates = Jinja2Templates(directory="templates")


async def htmx_http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> HTMLResponse | JSONResponse:
    """
    Handler wyjątku HTTPException — rozróżnia requesty HTMX od zwykłych.

    Jeśli żądanie pochodzi z HTMX (nagłówek `HX-Request: true`), zwróci
    HTML partial z komunikatem błędu (klasy DaisyUI: alert alert-error).
    W przeciwnym razie zwraca standardową odpowiedź JSON FastAPI.

    Args:
        request: Obiekt żądania HTTP.
        exc: Wyjątek HTTPException z kodem statusu i komunikatem.

    Returns:
        HTMLResponse z partiałem błędu (HTMX) lub JSONResponse (REST).
    """
    # Sprawdzamy nagłówek HTMX — automatycznie dodawany przez bibliotekę HTMX 2.0
    is_htmx: bool = request.headers.get("HX-Request") == "true"

    if is_htmx:
        # Dla HTMX zwracamy HTML partial — zostanie wstrzyknięty do DOM
        logger.warning(
            "HTTP %d dla HTMX request %s: %s",
            exc.status_code,
            request.url.path,
            exc.detail,
        )
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": exc.detail},
            status_code=exc.status_code,
        )

    # Dla zwykłych requestów zwracamy JSON zgodny ze standardem FastAPI
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def htmx_generic_exception_handler(
    request: Request,
    exc: Exception,
) -> HTMLResponse | JSONResponse:
    """
    Catch-all handler dla nieobsłużonych wyjątków (status 500).

    Loguje pełny traceback na poziomie ERROR. Nigdy nie ujawnia
    szczegółów błędu klientowi (ochrona przed information disclosure).
    Dla HTMX zwraca HTML partial, dla REST — JSON.

    Args:
        request: Obiekt żądania HTTP.
        exc: Dowolny nieoczekiwany wyjątek.

    Returns:
        HTMLResponse (HTMX) lub JSONResponse (REST) z kodem 500.
    """
    # Logujemy pełny traceback — widoczny tylko w logach serwera
    logger.exception(
        "Nieobsłużony wyjątek dla %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )

    # Generyczny komunikat — nie ujawniamy szczegółów stacktrace klientowi
    GENERIC_MESSAGE = "Wystąpił nieoczekiwany błąd serwera. Spróbuj ponownie później."

    is_htmx: bool = request.headers.get("HX-Request") == "true"

    if is_htmx:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": GENERIC_MESSAGE},
            status_code=500,
        )

    return JSONResponse(
        status_code=500,
        content={"detail": GENERIC_MESSAGE},
    )
