"""
Główna aplikacja FastAPI — moduł Projekty.

Dostępna przez Nginx pod /modules/projekty/. Zwraca HTML partiale (nie pełne dokumenty),
które HTMX wstawia do #main-content w Shell. Autoryzacja przez nagłówki X-User-*
przekazywane przez Shell middleware (BFF pattern).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud
from db import Base, SessionLocal, engine, get_db
from models import PortProtocol, ProjectStatus, ScopeCategory, ServerStatus, ServerType, TechnologyCategory
from schemas import (
    KPICreate,
    KPIUpdate,
    PortCreate,
    PortUpdate,
    ProjectCreate,
    ProjectUpdate,
    ScopeItemCreate,
    ScopeItemUpdate,
    ServerCreate,
    ServerUpdate,
    TechnologyCreate,
    TechnologyUpdate,
)


# ---------------------------------------------------------------------------
# Cykl życia aplikacji
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Zarządzanie cyklem życia — tworzenie tabel przy starcie."""
    # Tworzymy tabele, jeśli nie istnieją (migracje Alembic są preferowane w produkcji)
    Base.metadata.create_all(bind=engine)
    yield


# ---------------------------------------------------------------------------
# Inicjalizacja aplikacji FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="IT Project OS — Module Projekty",
    description="Moduł zarządzania projektami IT. Zwraca HTML partiale (HTMX).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Katalog szablonów Jinja2 — wyłącznie partiale HTML, nigdy pełne dokumenty
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Funkcja pomocnicza — odczyt tożsamości z nagłówków BFF
# ---------------------------------------------------------------------------


def _get_current_user(request: Request) -> dict[str, str]:
    """Odczytuje dane zalogowanego użytkownika z nagłówków HTTP (BFF pattern).

    Shell middleware przekazuje claims OIDC jako nagłówki X-User-*.
    Jeśli nagłówki nie są obecne, zwraca dane anonimowego użytkownika.

    Args:
        request: Obiekt Request FastAPI.

    Returns:
        Słownik z polami sub, email, name.
    """
    return {
        "sub": request.headers.get("X-User-Sub", "anonymous"),
        "email": request.headers.get("X-User-Email", ""),
        "name": request.headers.get("X-User-Name", "Anonim"),
    }


# ---------------------------------------------------------------------------
# Pomocnicze — konwersja pustych stringów z formularza HTML na None
# ---------------------------------------------------------------------------


def _none_if_empty(value: str | None) -> str | None:
    """Zamienia pusty string na None — formularze HTML wysyłają '' zamiast None."""
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _int_or_none(value: str | None) -> int | None:
    """Konwertuje string na int lub None — obsługuje puste pola liczbowe z formularzy HTML."""
    v = _none_if_empty(value)
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return None


# ===========================================================================
# ENDPOINTY — kolejność definicji jest kluczowa!
# Ścieżki statyczne  MUSZĄ być przed parametrycznymi /{project_id}/
# ===========================================================================


# ---------------------------------------------------------------------------
# 1. GET /  — strona główna (lista projektów)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def projects_home(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Strona główna modułu — wyświetla listę wszystkich projektów.

    Endpoint główny dostępny przez Nginx pod /modules/projekty/.
    Zwraca partial HTML do wstawienia przez HTMX do #main-content.

    Args:
        request: Obiekt Request FastAPI.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem list.html.
    """
    # Pobieramy wszystkie projekty bez filtrowania
    projects = crud.get_projects(db)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "projects": projects,
            "statuses": list(ProjectStatus),
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 2. GET /list  — lista projektów z opcjonalnym filtrem statusu
# ---------------------------------------------------------------------------


@app.get("/list", response_class=HTMLResponse)
def projects_list(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Lista projektów z opcjonalnym filtrem ?status=.

    Args:
        request: Obiekt Request FastAPI.
        status: Opcjonalny filtr statusu projektu (query param).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem list.html.
    """
    # Stosujemy filtr statusu, jeśli podany w query string
    projects = crud.get_projects(db, status=status)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "projects": projects,
            "statuses": list(ProjectStatus),
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 3. GET /create  — formularz nowego projektu
# ---------------------------------------------------------------------------


@app.get("/create", response_class=HTMLResponse)
def create_project_form(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz tworzenia nowego projektu.

    Pobiera listę aktywnych serwerów do wypełnienia select-boxów
    dla serwera DEV i PROD.

    Args:
        request: Obiekt Request FastAPI.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem form.html (partial).
    """
    # Pobieramy tylko aktywne serwery — serve jako opcje select w formularzu
    servers = crud.get_servers(db, status="Aktywny")
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "project": None,
            "statuses": list(ProjectStatus),
            "servers": servers,
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 4. POST /create  — przetwarzanie formularza nowego projektu
# ---------------------------------------------------------------------------


@app.post("/create", response_class=HTMLResponse)
def create_project_submit(
    request: Request,
    name: Annotated[str, Form()],
    code: Annotated[str, Form()],
    # status jest opcjonalne — formularz tworzenia go nie wysyła (domyślnie NOWY)
    status: Annotated[str | None, Form()] = None,
    owner_name: Annotated[str | None, Form()] = None,
    problem_statement: Annotated[str | None, Form()] = None,
    start_date: Annotated[str | None, Form()] = None,
    end_date: Annotated[str | None, Form()] = None,
    dev_server_id: Annotated[str | None, Form()] = None,
    prod_server_id: Annotated[str | None, Form()] = None,
    port_range_start: Annotated[str | None, Form()] = None,
    port_range_end: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Przetwarza formularz tworzenia projektu i przekierowuje do listy.

    Konwertuje puste stringi na None, waliduje przez Pydantic ProjectCreate,
    zapisuje do bazy i zwraca odświeżoną listę projektów.

    Args:
        request: Obiekt Request FastAPI.
        name: Nazwa projektu (wymagana).
        code: Unikalny kod projektu (wymagany).
        status: Status projektu (opcjonalne — formularz tworzenia go nie wysyła, domyślnie NOWY).
        owner_name: Imię właściciela (opcjonalne).
        problem_statement: Opis problemu/celu projektu (opcjonalne).
        start_date: Data rozpoczęcia w formacie YYYY-MM-DD (opcjonalne).
        end_date: Data zakończenia w formacie YYYY-MM-DD (opcjonalne).
        dev_server_id: ID serwera DEV (opcjonalne).
        prod_server_id: ID serwera PROD (opcjonalne).
        port_range_start: Początek zakresu portów (opcjonalne).
        port_range_end: Koniec zakresu portów (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem list.html po pomyślnym zapisie.
    """
    # Pobieramy dane użytkownika z nagłówków BFF
    current_user = _get_current_user(request)
    # Walidacja przez Pydantic — konwertujemy puste stringi na None
    from datetime import date as date_type
    project_data = ProjectCreate(
        name=name,
        code=code,
        # Jeśli status nie przyszedł z formularza (nowy projekt), używamy domyślnego NOWY
        status=ProjectStatus(status) if _none_if_empty(status) else ProjectStatus.NOWY,
        owner_name=_none_if_empty(owner_name),
        owner_id=current_user["sub"] if current_user["sub"] != "anonymous" else None,
        problem_statement=_none_if_empty(problem_statement),
        start_date=date_type.fromisoformat(start_date) if _none_if_empty(start_date) else None,
        end_date=date_type.fromisoformat(end_date) if _none_if_empty(end_date) else None,
        dev_server_id=_int_or_none(dev_server_id),
        prod_server_id=_int_or_none(prod_server_id),
        port_range_start=_int_or_none(port_range_start),
        port_range_end=_int_or_none(port_range_end),
    )
    # Zapisujemy projekt do bazy danych
    crud.create_project(db, project_data)
    # Zwracamy odświeżoną listę projektów
    projects = crud.get_projects(db)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "projects": projects,
            "statuses": list(ProjectStatus),
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 5. GET /servers  — lista serwerów
# ---------------------------------------------------------------------------


@app.get("/servers", response_class=HTMLResponse)
def servers_list(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Lista wszystkich serwerów infrastrukturalnych.

    Args:
        request: Obiekt Request FastAPI.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem servers/list.html (partial).
    """
    # Pobieramy wszystkie serwery posortowane alfabetycznie
    servers = crud.get_servers(db)
    return templates.TemplateResponse(
        request,
        "servers/list.html",
        {
            "servers": servers,
            "server_types": list(ServerType),
            "active_section": "servers",
        },
    )


# ---------------------------------------------------------------------------
# 6. GET /servers/create  — formularz nowego serwera
# ---------------------------------------------------------------------------


@app.get("/servers/create", response_class=HTMLResponse)
def create_server_form(
    request: Request,
) -> HTMLResponse:
    """Formularz tworzenia nowego serwera infrastrukturalnego.

    Args:
        request: Obiekt Request FastAPI.

    Returns:
        HTMLResponse z renderowanym szablonem servers/form.html (partial).
    """
    return templates.TemplateResponse(
        request,
        "servers/form.html",
        {
            "server": None,
            "server_types": list(ServerType),
            "server_statuses": list(ServerStatus),
            "active_section": "servers",
        },
    )


# ---------------------------------------------------------------------------
# 7. POST /servers/create  — przetwarzanie formularza nowego serwera
# ---------------------------------------------------------------------------


@app.post("/servers/create", response_class=HTMLResponse)
def create_server_submit(
    request: Request,
    name: Annotated[str, Form()],
    hostname: Annotated[str, Form()],
    server_type: Annotated[str, Form()],
    operating_system: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    status: Annotated[str, Form()] = "Aktywny",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Przetwarza formularz tworzenia serwera i zwraca odświeżoną listę.

    Args:
        request: Obiekt Request FastAPI.
        name: Unikalna nazwa serwera.
        hostname: Adres IP lub hostname.
        server_type: Typ środowiska (Dev/Staging/Prod/Shared).
        operating_system: System operacyjny (opcjonalne).
        description: Opis serwera (opcjonalne).
        status: Status aktywności serwera.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem servers/list.html po zapisie.
    """
    # Walidacja danych wejściowych przez Pydantic
    server_data = ServerCreate(
        name=name,
        hostname=hostname,
        server_type=ServerType(server_type),
        operating_system=_none_if_empty(operating_system),
        description=_none_if_empty(description),
        status=ServerStatus(status),
    )
    # Zapisujemy serwer do bazy danych
    crud.create_server(db, server_data)
    # Zwracamy odświeżoną listę serwerów
    servers = crud.get_servers(db)
    return templates.TemplateResponse(
        request,
        "servers/list.html",
        {
            "servers": servers,
            "server_types": list(ServerType),
            "active_section": "servers",
        },
    )


# ---------------------------------------------------------------------------
# 8. GET /servers/{sid}  — szczegóły serwera
# ---------------------------------------------------------------------------


@app.get("/servers/{sid}", response_class=HTMLResponse)
def server_detail(
    request: Request,
    sid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Karta szczegółów serwera z listą przypisanych projektów.

    Args:
        request: Obiekt Request FastAPI.
        sid: ID serwera.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem servers/detail.html lub not_found.html.
    """
    # Pobieramy serwer po ID
    server = crud.get_server_by_id(db, sid)
    if server is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Serwer o ID {sid} nie istnieje."},
            status_code=404,
        )
    # Pobieramy projekty korzystające z tego serwera (jako DEV lub PROD)
    all_projects = crud.get_projects(db)
    related_projects = [
        p for p in all_projects
        if p.dev_server_id == sid or p.prod_server_id == sid
    ]
    return templates.TemplateResponse(
        request,
        "servers/detail.html",
        {
            "server": server,
            "related_projects": related_projects,
            "active_section": "servers",
        },
    )


# ---------------------------------------------------------------------------
# 9. GET /servers/{sid}/edit  — formularz edycji serwera
# ---------------------------------------------------------------------------


@app.get("/servers/{sid}/edit", response_class=HTMLResponse)
def edit_server_form(
    request: Request,
    sid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz edycji istniejącego serwera.

    Args:
        request: Obiekt Request FastAPI.
        sid: ID serwera do edycji.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem servers/form.html lub not_found.html.
    """
    # Pobieramy serwer po ID
    server = crud.get_server_by_id(db, sid)
    if server is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Serwer o ID {sid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "servers/form.html",
        {
            "server": server,
            "server_types": list(ServerType),
            "server_statuses": list(ServerStatus),
            "active_section": "servers",
        },
    )


# ---------------------------------------------------------------------------
# 10. PUT /servers/{sid}  — zapis edycji serwera
# ---------------------------------------------------------------------------


@app.put("/servers/{sid}", response_class=HTMLResponse)
def update_server_submit(
    request: Request,
    sid: int,
    name: Annotated[str | None, Form()] = None,
    hostname: Annotated[str | None, Form()] = None,
    server_type: Annotated[str | None, Form()] = None,
    operating_system: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    status: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Aktualizuje dane serwera i zwraca odświeżoną listę.

    Args:
        request: Obiekt Request FastAPI.
        sid: ID serwera do aktualizacji.
        name: Nowa nazwa serwera (opcjonalne).
        hostname: Nowy hostname (opcjonalne).
        server_type: Nowy typ środowiska (opcjonalne).
        operating_system: Nowy system operacyjny (opcjonalne).
        description: Nowy opis (opcjonalne).
        status: Nowy status (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem servers/list.html lub not_found.html.
    """
    # Budujemy słownik tylko z ustawionymi polami, żeby zachować partial update
    update_kwargs: dict = {}
    if _none_if_empty(name) is not None:
        update_kwargs["name"] = name
    if _none_if_empty(hostname) is not None:
        update_kwargs["hostname"] = hostname
    if _none_if_empty(server_type) is not None:
        update_kwargs["server_type"] = ServerType(server_type)
    if _none_if_empty(operating_system) is not None:
        update_kwargs["operating_system"] = operating_system
    if description is not None:
        update_kwargs["description"] = _none_if_empty(description)
    if _none_if_empty(status) is not None:
        update_kwargs["status"] = ServerStatus(status)
    # Aktualizujemy serwer  
    updated = crud.update_server(db, sid, ServerUpdate(**update_kwargs))
    if updated is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Serwer o ID {sid} nie istnieje."},
            status_code=404,
        )
    # Zwracamy odświeżoną listę serwerów
    servers = crud.get_servers(db)
    return templates.TemplateResponse(
        request,
        "servers/list.html",
        {
            "servers": servers,
            "server_types": list(ServerType),
            "active_section": "servers",
        },
    )


# ---------------------------------------------------------------------------
# 11. DELETE /servers/{sid}  — usunięcie serwera
# ---------------------------------------------------------------------------


@app.delete("/servers/{sid}")
def delete_server_endpoint(sid: int, db: Session = Depends(get_db)) -> Response:
    """Usuwa serwer z bazy danych.

    HTMX używa hx-swap="outerHTML" na wierszu listy — pusty response usuwa element z DOM.

    Args:
        sid: ID serwera do usunięcia.
        db: Sesja bazy danych z Depends.

    Returns:
        Pusty Response 200 — HTMX outerHTML swap usuwa wiersz z listy.
    """
    # Usuwamy serwer (cascade zeruje FK w projektach)
    crud.delete_server(db, sid)
    return Response(content="", status_code=200)


# ---------------------------------------------------------------------------
# 12. GET /{project_id}  — karta projektu
# WAŻNE: Ten endpoint MUSI być po wszystkich statycznych ścieżkach /servers/...
# ---------------------------------------------------------------------------


@app.get("/{project_id}", response_class=HTMLResponse)
def project_detail(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Karta projektu z trzema sekcjami (opis, stos, zakres) i infrastrukturą.

    Ładuje projekt z eager-loaded relacjami (kpis, technologies, scope_items, ports).

    Args:
        request: Obiekt Request FastAPI.
        project_id: ID projektu.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem detail.html lub not_found.html.
    """
    # Pobieramy projekt z eager-loaded relacjami (unikamy N+1 queries)
    project = crud.get_project_by_id(db, project_id)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {project_id} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "detail.html",
        {
            "project": project,
            "tech_categories": list(TechnologyCategory),
            "scope_categories": list(ScopeCategory),
            "protocols": list(PortProtocol),
            "statuses": list(ProjectStatus),
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 13. GET /{project_id}/edit  — formularz edycji projektu
# ---------------------------------------------------------------------------


@app.get("/{project_id}/edit", response_class=HTMLResponse)
def edit_project_form(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz edycji istniejącego projektu.

    Args:
        request: Obiekt Request FastAPI.
        project_id: ID projektu do edycji.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem form.html lub not_found.html.
    """
    # Pobieramy projekt do edycji
    project = crud.get_project_by_id(db, project_id)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {project_id} nie istnieje."},
            status_code=404,
        )
    # Pobieramy aktywne serwery dla select-boxów
    servers = crud.get_servers(db, status="Aktywny")
    return templates.TemplateResponse(
        request,
        "form.html",
        {
            "project": project,
            "statuses": list(ProjectStatus),
            "servers": servers,
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 14. PUT /{project_id}  — zapis edycji projektu
# ---------------------------------------------------------------------------


@app.put("/{project_id}", response_class=HTMLResponse)
def update_project_submit(
    request: Request,
    project_id: int,
    name: Annotated[str | None, Form()] = None,
    code: Annotated[str | None, Form()] = None,
    status: Annotated[str | None, Form()] = None,
    owner_name: Annotated[str | None, Form()] = None,
    problem_statement: Annotated[str | None, Form()] = None,
    start_date: Annotated[str | None, Form()] = None,
    end_date: Annotated[str | None, Form()] = None,
    dev_server_id: Annotated[str | None, Form()] = None,
    prod_server_id: Annotated[str | None, Form()] = None,
    port_range_start: Annotated[str | None, Form()] = None,
    port_range_end: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Aktualizuje dane projektu i zwraca odświeżoną listę.

    Args:
        request: Obiekt Request FastAPI.
        project_id: ID projektu do aktualizacji.
        Pozostałe pola: opcjonalne dane do aktualizacji z formularza.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem list.html lub not_found.html.
    """
    from datetime import date as date_type
    # Budujemy kwargs tylko z podanych pól — zachowujemy partial update
    update_kwargs: dict = {}
    if _none_if_empty(name) is not None:
        update_kwargs["name"] = name
    if _none_if_empty(code) is not None:
        update_kwargs["code"] = code
    if _none_if_empty(status) is not None:
        update_kwargs["status"] = ProjectStatus(status)
    # Opcjonalne pola tekstowe — None jeśli puste
    update_kwargs["owner_name"] = _none_if_empty(owner_name)
    update_kwargs["problem_statement"] = _none_if_empty(problem_statement)
    # Daty — parsujemy z ISO 8601 lub None
    update_kwargs["start_date"] = (
        date_type.fromisoformat(start_date) if _none_if_empty(start_date) else None
    )
    update_kwargs["end_date"] = (
        date_type.fromisoformat(end_date) if _none_if_empty(end_date) else None
    )
    # Pola liczbowe — None jeśli puste
    update_kwargs["dev_server_id"] = _int_or_none(dev_server_id)
    update_kwargs["prod_server_id"] = _int_or_none(prod_server_id)
    update_kwargs["port_range_start"] = _int_or_none(port_range_start)
    update_kwargs["port_range_end"] = _int_or_none(port_range_end)

    # Aktualizujemy projekt
    updated = crud.update_project(db, project_id, ProjectUpdate(**update_kwargs))
    if updated is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {project_id} nie istnieje."},
            status_code=404,
        )
    # Zwracamy odświeżoną listę projektów
    projects = crud.get_projects(db)
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "projects": projects,
            "statuses": list(ProjectStatus),
            "active_section": "projects",
        },
    )


# ---------------------------------------------------------------------------
# 15. DELETE /{project_id}  — usunięcie projektu (cascade)
# ---------------------------------------------------------------------------


@app.delete("/{project_id}")
def delete_project_endpoint(project_id: int, db: Session = Depends(get_db)) -> Response:
    """Usuwa projekt z bazy danych wraz ze wszystkimi encjami potomnymi (cascade).

    HTMX używa hx-swap="outerHTML" na wierszu listy — pusty response usuwa element z DOM.

    Args:
        project_id: ID projektu do usunięcia.
        db: Sesja bazy danych z Depends.

    Returns:
        Pusty Response 200 — HTMX outerHTML swap usuwa wiersz z listy.
    """
    # Kaskadowe usunięcie obsługuje SQLAlchemy (cascade="all, delete-orphan" w modelu)
    crud.delete_project(db, project_id)
    return Response(content="", status_code=200)


# ===========================================================================
# ENDPOINTY — KPI (inline na karcie projektu)
# Wzorzec HTMX: POST → wiersz do wstawienia w tabeli; DELETE → pusty response
# ===========================================================================


@app.get("/{pid}/kpis/create", response_class=HTMLResponse)
def kpi_create_form(
    request: Request,
    pid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline tworzenia nowego KPI projektu.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/kpi_form.html.
    """
    # Sprawdzamy istnienie projektu przed renderowaniem formularza
    project = crud.get_project_by_id(db, pid)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {pid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/kpi_form.html",
        {"project_id": pid, "kpi": None},
    )


@app.post("/{pid}/kpis", response_class=HTMLResponse)
def kpi_create_submit(
    request: Request,
    pid: int,
    name: Annotated[str, Form()],
    target_value: Annotated[str, Form()],
    current_value: Annotated[str | None, Form()] = None,
    unit: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Tworzy nowy KPI i zwraca wiersz do wstawienia przez HTMX (hx-swap="beforeend").

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        name: Nazwa wskaźnika.
        target_value: Docelowa wartość.
        current_value: Aktualna wartość (opcjonalne).
        unit: Jednostka miary (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/kpi_row.html.
    """
    # Tworzymy KPI przypisany do projektu
    kpi_data = KPICreate(
        name=name,
        target_value=target_value,
        current_value=_none_if_empty(current_value),
        unit=_none_if_empty(unit),
    )
    kpi = crud.create_kpi(db, pid, kpi_data)
    return templates.TemplateResponse(
        request,
        "partials/kpi_row.html",
        {"kpi": kpi, "project_id": pid},
    )


@app.get("/{pid}/kpis/{kid}/edit", response_class=HTMLResponse)
def kpi_edit_form(
    request: Request,
    pid: int,
    kid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline edycji istniejącego KPI.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        kid: ID wskaźnika KPI do edycji.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/kpi_form.html.
    """
    # Pobieramy KPI do edycji
    kpi = crud.get_kpi_by_id(db, kid)
    if kpi is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"KPI o ID {kid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/kpi_form.html",
        {"kpi": kpi, "project_id": pid},
    )


@app.put("/{pid}/kpis/{kid}", response_class=HTMLResponse)
def kpi_update_submit(
    request: Request,
    pid: int,
    kid: int,
    name: Annotated[str | None, Form()] = None,
    target_value: Annotated[str | None, Form()] = None,
    current_value: Annotated[str | None, Form()] = None,
    unit: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Aktualizuje KPI i zwraca zaktualizowany wiersz dla HTMX swap.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        kid: ID wskaźnika KPI do aktualizacji.
        Pozostałe pola: dane do aktualizacji (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/kpi_row.html.
    """
    # Budujemy partial update — tylko podane pola
    update_kwargs: dict = {}
    if _none_if_empty(name) is not None:
        update_kwargs["name"] = name
    if _none_if_empty(target_value) is not None:
        update_kwargs["target_value"] = target_value
    update_kwargs["current_value"] = _none_if_empty(current_value)
    update_kwargs["unit"] = _none_if_empty(unit)
    # Aktualizujemy KPI
    kpi = crud.update_kpi(db, kid, KPIUpdate(**update_kwargs))
    if kpi is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"KPI o ID {kid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/kpi_row.html",
        {"kpi": kpi, "project_id": pid},
    )


@app.delete("/{pid}/kpis/{kid}")
def kpi_delete(pid: int, kid: int, db: Session = Depends(get_db)) -> Response:
    """Usuwa wskaźnik KPI.

    HTMX używa hx-swap="outerHTML" na wierszu — pusty response usuwa element z DOM.

    Args:
        pid: ID projektu nadrzędnego.
        kid: ID KPI do usunięcia.
        db: Sesja bazy danych z Depends.

    Returns:
        Pusty Response 200.
    """
    # Usuwamy KPI z bazy danych
    crud.delete_kpi(db, kid)
    return Response(content="", status_code=200)


# ===========================================================================
# ENDPOINTY — Technologie (inline na karcie projektu)
# ===========================================================================


@app.get("/{pid}/technologies/create", response_class=HTMLResponse)
def tech_create_form(
    request: Request,
    pid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline dodania nowej technologii do stos projektu.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/tech_form.html.
    """
    # Sprawdzamy istnienie projektu przed renderowaniem formularza
    project = crud.get_project_by_id(db, pid)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {pid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/tech_form.html",
        {
            "project_id": pid,
            "tech": None,
            "tech_categories": list(TechnologyCategory),
        },
    )


@app.post("/{pid}/technologies", response_class=HTMLResponse)
def tech_create_submit(
    request: Request,
    pid: int,
    category: Annotated[str, Form()],
    name: Annotated[str, Form()],
    version: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Dodaje technologię do projektu i zwraca wiersz dla HTMX (hx-swap="beforeend").

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        category: Kategoria technologii.
        name: Nazwa technologii.
        version: Wersja (opcjonalna).
        description: Opis (opcjonalny).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/tech_row.html.
    """
    # Walidacja i zapis do bazy danych
    tech_data = TechnologyCreate(
        category=TechnologyCategory(category),
        name=name,
        version=_none_if_empty(version),
        description=_none_if_empty(description),
    )
    tech = crud.create_technology(db, pid, tech_data)
    return templates.TemplateResponse(
        request,
        "partials/tech_row.html",
        {
            "tech": tech,
            "project_id": pid,
            "tech_categories": list(TechnologyCategory),
        },
    )


@app.get("/{pid}/technologies/{tid}/edit", response_class=HTMLResponse)
def tech_edit_form(
    request: Request,
    pid: int,
    tid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline edycji technologii projektu.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        tid: ID technologii do edycji.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/tech_form.html.
    """
    # Pobieramy technologię do edycji
    tech = crud.get_technology_by_id(db, tid)
    if tech is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Technologia o ID {tid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/tech_form.html",
        {
            "tech": tech,
            "project_id": pid,
            "tech_categories": list(TechnologyCategory),
        },
    )


@app.put("/{pid}/technologies/{tid}", response_class=HTMLResponse)
def tech_update_submit(
    request: Request,
    pid: int,
    tid: int,
    category: Annotated[str | None, Form()] = None,
    name: Annotated[str | None, Form()] = None,
    version: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Aktualizuje technologię i zwraca zaktualizowany wiersz dla HTMX.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        tid: ID technologii do aktualizacji.
        Pozostałe pola: dane do aktualizacji (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/tech_row.html.
    """
    # Budujemy partial update — konwertujemy enum i puste stringi
    update_kwargs: dict = {}
    if _none_if_empty(category) is not None:
        update_kwargs["category"] = TechnologyCategory(category)
    if _none_if_empty(name) is not None:
        update_kwargs["name"] = name
    update_kwargs["version"] = _none_if_empty(version)
    update_kwargs["description"] = _none_if_empty(description)
    # Aktualizujemy technologię
    tech = crud.update_technology(db, tid, TechnologyUpdate(**update_kwargs))
    if tech is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Technologia o ID {tid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/tech_row.html",
        {
            "tech": tech,
            "project_id": pid,
            "tech_categories": list(TechnologyCategory),
        },
    )


@app.delete("/{pid}/technologies/{tid}")
def tech_delete(pid: int, tid: int, db: Session = Depends(get_db)) -> Response:
    """Usuwa technologię z projektu.

    HTMX używa hx-swap="outerHTML" — pusty response usuwa wiersz z DOM.

    Args:
        pid: ID projektu nadrzędnego.
        tid: ID technologii do usunięcia.
        db: Sesja bazy danych z Depends.

    Returns:
        Pusty Response 200.
    """
    # Usuwamy technologię z bazy danych
    crud.delete_technology(db, tid)
    return Response(content="", status_code=200)


# ===========================================================================
# ENDPOINTY — Scope Items (inline na karcie projektu)
# ===========================================================================


@app.get("/{pid}/scope/create", response_class=HTMLResponse)
def scope_create_form(
    request: Request,
    pid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline dodania nowego elementu zakresu projektu.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/scope_form.html.
    """
    # Sprawdzamy istnienie projektu przed renderowaniem formularza
    project = crud.get_project_by_id(db, pid)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {pid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/scope_form.html",
        {
            "project_id": pid,
            "item": None,
            "scope_categories": list(ScopeCategory),
        },
    )


@app.post("/{pid}/scope", response_class=HTMLResponse)
def scope_create_submit(
    request: Request,
    pid: int,
    category: Annotated[str, Form()],
    description: Annotated[str, Form()],
    priority: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Dodaje element zakresu i zwraca wiersz dla HTMX (hx-swap="beforeend").

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        category: Kategoria zakresu.
        description: Opis elementu zakresu.
        priority: Priorytet/kolejność (opcjonalny).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/scope_row.html.
    """
    # Walidacja i zapis do bazy danych
    item_data = ScopeItemCreate(
        category=ScopeCategory(category),
        description=description,
        priority=_int_or_none(priority),
    )
    item = crud.create_scope_item(db, pid, item_data)
    return templates.TemplateResponse(
        request,
        "partials/scope_row.html",
        {
            "item": item,
            "project_id": pid,
            "scope_categories": list(ScopeCategory),
        },
    )


@app.get("/{pid}/scope/{sid}/edit", response_class=HTMLResponse)
def scope_edit_form(
    request: Request,
    pid: int,
    sid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline edycji elementu zakresu projektu.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        sid: ID elementu zakresu do edycji.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/scope_form.html.
    """
    # Pobieramy element zakresu do edycji
    item = crud.get_scope_item_by_id(db, sid)
    if item is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Element zakresu o ID {sid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/scope_form.html",
        {
            "item": item,
            "project_id": pid,
            "scope_categories": list(ScopeCategory),
        },
    )


@app.put("/{pid}/scope/{sid}", response_class=HTMLResponse)
def scope_update_submit(
    request: Request,
    pid: int,
    sid: int,
    category: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    priority: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Aktualizuje element zakresu i zwraca zaktualizowany wiersz dla HTMX.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        sid: ID elementu zakresu do aktualizacji.
        Pozostałe pola: dane do aktualizacji (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/scope_row.html.
    """
    # Budujemy partial update — konwertujemy enumy i puste stringi
    update_kwargs: dict = {}
    if _none_if_empty(category) is not None:
        update_kwargs["category"] = ScopeCategory(category)
    if _none_if_empty(description) is not None:
        update_kwargs["description"] = description
    update_kwargs["priority"] = _int_or_none(priority)
    # Aktualizujemy element zakresu
    item = crud.update_scope_item(db, sid, ScopeItemUpdate(**update_kwargs))
    if item is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Element zakresu o ID {sid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/scope_row.html",
        {
            "item": item,
            "project_id": pid,
            "scope_categories": list(ScopeCategory),
        },
    )


@app.delete("/{pid}/scope/{sid}")
def scope_delete(pid: int, sid: int, db: Session = Depends(get_db)) -> Response:
    """Usuwa element zakresu projektu.

    HTMX używa hx-swap="outerHTML" — pusty response usuwa wiersz z DOM.

    Args:
        pid: ID projektu nadrzędnego.
        sid: ID elementu zakresu do usunięcia.
        db: Sesja bazy danych z Depends.

    Returns:
        Pusty Response 200.
    """
    # Usuwamy element zakresu z bazy danych
    crud.delete_scope_item(db, sid)
    return Response(content="", status_code=200)


# ===========================================================================
# ENDPOINTY — Porty (inline na karcie projektu)
# ===========================================================================


@app.get("/{pid}/ports/create", response_class=HTMLResponse)
def port_create_form(
    request: Request,
    pid: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline dodania nowego portu sieciowego do projektu.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/port_form.html.
    """
    # Sprawdzamy istnienie projektu przed renderowaniem formularza
    project = crud.get_project_by_id(db, pid)
    if project is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Projekt o ID {pid} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/port_form.html",
        {
            "project_id": pid,
            "port": None,
            "protocols": list(PortProtocol),
        },
    )


@app.post("/{pid}/ports", response_class=HTMLResponse)
def port_create_submit(
    request: Request,
    pid: int,
    port_number: Annotated[str, Form()],
    protocol: Annotated[str, Form()],
    service_name: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Przypisuje port do projektu i zwraca wiersz dla HTMX (hx-swap="beforeend").

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        port_number: Numer portu (1-65535).
        protocol: Protokół (TCP/UDP/TCP/UDP).
        service_name: Nazwa usługi (opcjonalna).
        description: Opis przeznaczenia portu (opcjonalny).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/port_row.html.
    """
    # Walidacja i zapis do bazy danych
    port_data = PortCreate(
        port_number=int(port_number),
        protocol=PortProtocol(protocol),
        service_name=_none_if_empty(service_name),
        description=_none_if_empty(description),
    )
    port = crud.create_port(db, pid, port_data)
    return templates.TemplateResponse(
        request,
        "partials/port_row.html",
        {
            "port": port,
            "project_id": pid,
            "protocols": list(PortProtocol),
        },
    )


@app.get("/{pid}/ports/{port_id}/edit", response_class=HTMLResponse)
def port_edit_form(
    request: Request,
    pid: int,
    port_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Formularz inline edycji portu sieciowego.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        port_id: ID portu do edycji.
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/port_form.html.
    """
    # Pobieramy port do edycji
    port = crud.get_port_by_id(db, port_id)
    if port is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Port o ID {port_id} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/port_form.html",
        {
            "port": port,
            "project_id": pid,
            "protocols": list(PortProtocol),
        },
    )


@app.put("/{pid}/ports/{port_id}", response_class=HTMLResponse)
def port_update_submit(
    request: Request,
    pid: int,
    port_id: int,
    port_number: Annotated[str | None, Form()] = None,
    protocol: Annotated[str | None, Form()] = None,
    service_name: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Aktualizuje port sieciowy i zwraca zaktualizowany wiersz dla HTMX.

    Args:
        request: Obiekt Request FastAPI.
        pid: ID projektu nadrzędnego.
        port_id: ID portu do aktualizacji.
        Pozostałe pola: dane do aktualizacji (opcjonalne).
        db: Sesja bazy danych z Depends.

    Returns:
        HTMLResponse z renderowanym szablonem partials/port_row.html.
    """
    # Budujemy partial update — konwertujemy puste stringi i enumy
    update_kwargs: dict = {}
    if _int_or_none(port_number) is not None:
        update_kwargs["port_number"] = int(port_number)  # type: ignore[arg-type]
    if _none_if_empty(protocol) is not None:
        update_kwargs["protocol"] = PortProtocol(protocol)
    update_kwargs["service_name"] = _none_if_empty(service_name)
    update_kwargs["description"] = _none_if_empty(description)
    # Aktualizujemy port
    port = crud.update_port(db, port_id, PortUpdate(**update_kwargs))
    if port is None:
        return templates.TemplateResponse(
            request,
            "partials/not_found.html",
            {"message": f"Port o ID {port_id} nie istnieje."},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "partials/port_row.html",
        {
            "port": port,
            "project_id": pid,
            "protocols": list(PortProtocol),
        },
    )


@app.delete("/{pid}/ports/{port_id}")
def port_delete(pid: int, port_id: int, db: Session = Depends(get_db)) -> Response:
    """Usuwa port sieciowy z projektu.

    HTMX używa hx-swap="outerHTML" — pusty response usuwa wiersz z DOM.

    Args:
        pid: ID projektu nadrzędnego.
        port_id: ID portu do usunięcia.
        db: Sesja bazy danych z Depends.

    Returns:
        Pusty Response 200.
    """
    # Usuwamy port z bazy danych
    crud.delete_port(db, port_id)
    return Response(content="", status_code=200)
