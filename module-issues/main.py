"""
Główna aplikacja FastAPI — moduł Issues.

Dostępna przez Nginx pod /modules/issues/. Zwraca HTML partiale (nie pełne dokumenty),
które HTMX wstawia do #main-content w Shell. Autoryzacja przez nagłówki X-User-* 
przekazywane przez Shell middleware (Podejście A — BFF).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import get_settings
from crud import (
    create_issue,
    delete_issue,
    get_issue_by_id,
    get_issues,
    update_issue,
)
from db import Base, engine, get_db
from models import IssuePriority, IssueStatus
from schemas import IssueCreate, IssueUpdate


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Zarządzanie cyklem życia aplikacji — tworzenie tabel przy starcie."""
    Base.metadata.create_all(bind=engine)
    yield


# Inicjalizacja aplikacji FastAPI z jawną konfiguracją Swagger UI i ReDoc
app = FastAPI(
    title="IT Project OS — Module Issues",
    description="Moduł zarządzania zgłoszeniami. Zwraca HTML partiale (HTMX).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Silnik szablonów Jinja2 — katalog templates względem katalogu serwisu
templates = Jinja2Templates(directory="templates")


def _get_current_user(request: Request) -> dict[str, str]:
    """
    Odczytuje dane zalogowanego użytkownika z nagłówków HTTP.

    Shell middleware dodaje nagłówki X-User-Sub, X-User-Email, X-User-Name
    do każdego żądania proxowanego do modułu (Podejście A — BFF pattern).

    Args:
        request: Obiekt żądania FastAPI.

    Returns:
        Słownik z kluczami: sub, email, name.
    """
    return {
        "sub": request.headers.get("X-User-Sub", "anonymous"),
        "email": request.headers.get("X-User-Email", ""),
        "name": request.headers.get("X-User-Name", "Anonim"),
    }


@app.get("/", response_class=HTMLResponse)
async def issues_home(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    """
    Strona główna modułu — lista zgłoszeń.

    Zwraca HTML partial ładowany do #main-content przez HTMX.
    """
    issues = get_issues(db)
    return templates.TemplateResponse(
        request,
        "list.html",
        {"issues": issues},
    )


@app.get("/list", response_class=HTMLResponse)
async def issues_list(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
) -> HTMLResponse:
    """
    Endpoint listy zgłoszeń z opcjonalnym filtrem statusu.

    Parametr query ?status=Nowy pozwala filtrować wyniki po statusie.
    """
    # Pobieramy zgłoszenia z opcjonalnym filtrem
    issues = get_issues(db, status=status)
    return templates.TemplateResponse(
        request,
        "list.html",
        {"issues": issues},
    )


@app.get("/create", response_class=HTMLResponse)
async def create_issue_form(request: Request) -> HTMLResponse:
    """Formularz tworzenia nowego zgłoszenia — HTML partial."""
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            # Przekazujemy enumy do szablonu dla budowania selectów
            "issue": None,
            "priorities": list(IssuePriority),
            "statuses": list(IssueStatus),
        },
    )


@app.post("/create", response_class=HTMLResponse)
async def create_issue_submit(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    priority: Annotated[str, Form()] = IssuePriority.SREDNI.value,
    assignee_id: Annotated[str | None, Form()] = None,
    assignee_name: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Obsługa formularza tworzenia zgłoszenia (HTMX hx-post).

    Po pomyślnym utworzeniu zwraca zaktualizowaną listę zgłoszeń.
    """
    # Odczytujemy dane zalogowanego użytkownika z nagłówków
    user = _get_current_user(request)

    # Walidacja danych przez schemat Pydantic
    issue_data = IssueCreate(
        title=title,
        description=description or None,
        priority=IssuePriority(priority),
        assignee_id=assignee_id or None,
        assignee_name=assignee_name or None,
    )

    # Tworzymy zgłoszenie w bazie
    create_issue(
        db=db,
        issue_data=issue_data,
        author_id=user["sub"],
        author_name=user["name"],
    )

    # Po created zwracamy odświeżoną listę (pattern Post/Redirect/Get przez HTMX)
    issues = get_issues(db)
    return templates.TemplateResponse(
        request,
        "list.html",
        {"issues": issues},
    )


@app.get("/{issue_id}", response_class=HTMLResponse)
async def issue_detail(
    request: Request,
    issue_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    """
    Szczegóły zgłoszenia — HTML partial z kartą DaisyUI.

    Zwraca 404 HTML partial jeśli zgłoszenie nie istnieje.
    """
    issue = get_issue_by_id(db, issue_id)
    if issue is None:
        # Zwracamy partial z błędem 404 zamiast wyjątku HTTP
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"issue_id": issue_id},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"issue": issue},
    )


@app.get("/{issue_id}/edit", response_class=HTMLResponse)
async def edit_issue_form(
    request: Request,
    issue_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> HTMLResponse:
    """Formularz edycji istniejącego zgłoszenia — HTML partial."""
    issue = get_issue_by_id(db, issue_id)
    if issue is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"issue_id": issue_id},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "issue": issue,
            "priorities": list(IssuePriority),
            "statuses": list(IssueStatus),
        },
    )


@app.put("/{issue_id}", response_class=HTMLResponse)
async def update_issue_submit(
    request: Request,
    issue_id: int,
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    status: Annotated[str | None, Form()] = None,
    priority: Annotated[str | None, Form()] = None,
    assignee_id: Annotated[str | None, Form()] = None,
    assignee_name: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """
    Aktualizacja zgłoszenia (HTMX hx-put) — partial update.

    Zwraca zaktualizowany wiersz tabeli (partial issue_row.html).
    """
    # Budujemy słownik tylko z niepustych pól
    update_kwargs: dict = {}
    if title is not None:
        update_kwargs["title"] = title
    if description is not None:
        update_kwargs["description"] = description
    if status is not None:
        update_kwargs["status"] = IssueStatus(status)
    if priority is not None:
        update_kwargs["priority"] = IssuePriority(priority)
    if assignee_id is not None:
        update_kwargs["assignee_id"] = assignee_id or None
    if assignee_name is not None:
        update_kwargs["assignee_name"] = assignee_name or None

    issue_data = IssueUpdate(**update_kwargs)
    updated = update_issue(db, issue_id, issue_data)

    if updated is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"issue_id": issue_id},
            status_code=404,
        )

    # Zwracamy zaktualizowaną listę — najprostsze podejście na MVP
    issues = get_issues(db)
    return templates.TemplateResponse(
        request,
        "list.html",
        {"issues": issues},
    )


@app.delete("/{issue_id}")
async def delete_issue_endpoint(
    issue_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """
    Usuwa zgłoszenie — HTMX hx-delete z hx-swap outerHTML.

    Zwraca pusty response 200 — HTMX podmienia element #issue-{id} na ""
    (efektywnie usuwa wiersz z tabeli bez przeładowania strony).
    """
    delete_issue(db, issue_id)
    # Pusty response powoduje usunięcie elementu przez HTMX (outerHTML swap)
    return Response(content="", status_code=200)
