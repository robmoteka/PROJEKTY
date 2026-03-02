"""
Schematy Pydantic dla modułu Projekty.

Zawiera klasy walidacji danych wejściowych (Create/Update)
oraz reprezentacji odpowiedzi API (Read) dla wszystkich encji modułu:
- Server     — serwery infrastrukturalne
- Project    — projekty IT
- ProjectKPI — wskaźniki sukcesu
- ProjectTechnology  — stos technologiczny
- ProjectScopeItem   — elementy zakresu
- ProjectPort        — porty sieciowe
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from models import (
    PortProtocol,
    ProjectStatus,
    ScopeCategory,
    ServerStatus,
    ServerType,
    TechnologyCategory,
)

# ---------------------------------------------------------------------------
# Schematy Serwera
# ---------------------------------------------------------------------------


class ServerCreate(BaseModel):
    """Dane wejściowe do utworzenia nowego serwera."""

    name: str = Field(..., min_length=2, max_length=255)
    hostname: str = Field(..., min_length=2, max_length=255)
    server_type: ServerType = ServerType.DEV
    operating_system: str | None = Field(None, max_length=100)
    description: str | None = None
    status: ServerStatus = ServerStatus.AKTYWNY


class ServerUpdate(BaseModel):
    """Dane do aktualizacji serwera — wszystkie pola opcjonalne (partial update)."""

    name: str | None = Field(None, min_length=2, max_length=255)
    hostname: str | None = Field(None, min_length=2, max_length=255)
    server_type: ServerType | None = None
    operating_system: str | None = None
    description: str | None = None
    status: ServerStatus | None = None


class ServerRead(BaseModel):
    """Reprezentacja serwera zwracana przez API."""

    id: int
    name: str
    hostname: str
    server_type: str
    operating_system: str | None
    description: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Schematy KPI — zdefiniowane przed ProjectRead (forwardref)
# ---------------------------------------------------------------------------


class KPICreate(BaseModel):
    """Dane wejściowe do utworzenia wskaźnika KPI projektu."""

    name: str = Field(..., min_length=2, max_length=255)
    target_value: str = Field(..., min_length=1, max_length=255)
    current_value: str | None = Field(None, max_length=255)
    unit: str | None = Field(None, max_length=50)


class KPIUpdate(BaseModel):
    """Dane do aktualizacji KPI — partial update, wszystkie pola opcjonalne."""

    name: str | None = Field(None, min_length=2, max_length=255)
    target_value: str | None = Field(None, min_length=1, max_length=255)
    current_value: str | None = None
    unit: str | None = None


class KPIRead(BaseModel):
    """Reprezentacja wskaźnika KPI zwracana przez API."""

    id: int
    project_id: int
    name: str
    target_value: str
    current_value: str | None
    unit: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Schematy Technologii — zdefiniowane przed ProjectRead (forwardref)
# ---------------------------------------------------------------------------


class TechnologyCreate(BaseModel):
    """Dane wejściowe do dodania technologii do stosu projektu."""

    category: TechnologyCategory = TechnologyCategory.BACKEND
    name: str = Field(..., min_length=1, max_length=255)
    version: str | None = Field(None, max_length=50)
    description: str | None = None


class TechnologyUpdate(BaseModel):
    """Dane do aktualizacji technologii — partial update."""

    category: TechnologyCategory | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    version: str | None = None
    description: str | None = None


class TechnologyRead(BaseModel):
    """Reprezentacja technologii zwracana przez API."""

    id: int
    project_id: int
    category: str
    name: str
    version: str | None
    description: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Schematy Zakresu (Scope Items) — zdefiniowane przed ProjectRead (forwardref)
# ---------------------------------------------------------------------------


class ScopeItemCreate(BaseModel):
    """Dane wejściowe do dodania elementu zakresu projektu."""

    category: ScopeCategory
    description: str = Field(..., min_length=3)
    priority: int | None = None


class ScopeItemUpdate(BaseModel):
    """Dane do aktualizacji elementu zakresu — partial update."""

    category: ScopeCategory | None = None
    description: str | None = Field(None, min_length=3)
    priority: int | None = None


class ScopeItemRead(BaseModel):
    """Reprezentacja elementu zakresu zwracana przez API."""

    id: int
    project_id: int
    category: str
    description: str
    priority: int | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Schematy Portów — zdefiniowane przed ProjectRead (forwardref)
# ---------------------------------------------------------------------------


class PortCreate(BaseModel):
    """Dane wejściowe do przypisania portu sieciowego do projektu."""

    port_number: int = Field(..., ge=1, le=65535)
    protocol: PortProtocol = PortProtocol.TCP
    service_name: str | None = Field(None, max_length=255)
    description: str | None = None


class PortUpdate(BaseModel):
    """Dane do aktualizacji portu — partial update."""

    port_number: int | None = Field(None, ge=1, le=65535)
    protocol: PortProtocol | None = None
    service_name: str | None = None
    description: str | None = None


class PortRead(BaseModel):
    """Reprezentacja portu sieciowego zwracana przez API."""

    id: int
    project_id: int
    port_number: int
    protocol: str
    service_name: str | None
    description: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Schematy Projektu — ProjectRead referencjonuje powyższe klasy *Read
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    """Dane wejściowe do utworzenia nowego projektu — sekcja 1 karty projektu."""

    # Pola wymagane
    name: str = Field(..., min_length=3, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)  # np. "PROJECT-X-2026"
    # Pola opcjonalne — pozostałe pola sekcji 1
    status: ProjectStatus = ProjectStatus.NOWY
    owner_name: str | None = Field(None, max_length=255)
    owner_id: str | None = None
    problem_statement: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    # Infrastruktura — powiązania z serwerami
    dev_server_id: int | None = None
    prod_server_id: int | None = None
    # Zakres portów przypisanych do projektu
    port_range_start: int | None = Field(None, ge=1, le=65535)
    port_range_end: int | None = Field(None, ge=1, le=65535)


class ProjectUpdate(BaseModel):
    """Dane do aktualizacji projektu — partial update, wszystkie pola opcjonalne."""

    name: str | None = Field(None, min_length=3, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=50)
    status: ProjectStatus | None = None
    owner_name: str | None = None
    owner_id: str | None = None
    problem_statement: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    dev_server_id: int | None = None
    prod_server_id: int | None = None
    port_range_start: int | None = Field(None, ge=1, le=65535)
    port_range_end: int | None = Field(None, ge=1, le=65535)


class ProjectRead(BaseModel):
    """Pełna reprezentacja projektu z zagnieżdżonymi relacjami zwracana przez API."""

    id: int
    name: str
    code: str
    status: str
    owner_name: str | None
    owner_id: str | None
    problem_statement: str | None
    start_date: date | None
    end_date: date | None
    dev_server_id: int | None
    prod_server_id: int | None
    # Zagnieżdżone obiekty powiązanych serwerów
    dev_server: ServerRead | None = None
    prod_server: ServerRead | None = None
    port_range_start: int | None
    port_range_end: int | None
    # Zagnieżdżone listy encji potomnych
    kpis: list[KPIRead] = []
    technologies: list[TechnologyRead] = []
    scope_items: list[ScopeItemRead] = []
    ports: list[PortRead] = []
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


# Odbudowanie modelu po pełnej definicji wszystkich klas zależnych
ProjectRead.model_rebuild()
