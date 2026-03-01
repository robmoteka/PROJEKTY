"""
Schematy Pydantic dla modułu Issues — walidacja danych wejściowych i wyjściowych.

Zawiera trzy główne klasy:
- IssueCreate: walidacja danych przy tworzeniu nowego zgłoszenia
- IssueUpdate: walidacja danych przy aktualizacji (partial update)
- IssueRead: reprezentacja zgłoszenia zwracana przez API
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models import IssuePriority, IssueStatus


class IssueCreate(BaseModel):
    """Dane wejściowe do utworzenia nowego zgłoszenia."""

    # Tytuł jest wymagany — minimum 3 znaki, maksimum 255
    title: str = Field(..., min_length=3, max_length=255)
    # Opis jest opcjonalny — może być null
    description: str | None = None
    # Priorytet domyślnie Średni
    priority: IssuePriority = IssuePriority.SREDNI
    # Opcjonalne przypisanie do użytkownika (claim `sub` z OIDC)
    assignee_id: str | None = None
    # Opcjonalna czytelna nazwa osoby przypisanej
    assignee_name: str | None = None


class IssueUpdate(BaseModel):
    """Dane wejściowe do aktualizacji zgłoszenia — wszystkie pola opcjonalne (PATCH-style)."""

    # Wszystkie pola opcjonalne — aktualizowany tylko pola, które zostały podane
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee_id: str | None = None
    assignee_name: str | None = None


class IssueRead(BaseModel):
    """Reprezentacja zgłoszenia zwracana przez API (response model)."""

    id: int
    title: str
    description: str | None
    status: str
    priority: str
    # Dane autora — opcjonalne, wypełniane z nagłówków X-User-Sub / X-User-Name
    author_id: str | None
    author_name: str | None
    # Dane osoby przypisanej — opcjonalne
    assignee_id: str | None
    assignee_name: str | None
    # Znaczniki czasu zarządzane przez bazę danych
    created_at: datetime | None
    updated_at: datetime | None

    # Pozwala tworzyć instancję bezpośrednio z obiektu SQLAlchemy
    model_config = {"from_attributes": True}
