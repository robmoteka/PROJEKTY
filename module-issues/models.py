"""
Modele ORM modułu Module Issues.

Zawiera modele SQLAlchemy reprezentujące tabele bazy danych:
- Issue: zgłoszenia/zadania w systemie zarządzania projektami IT
"""

from __future__ import annotations

import enum

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from db import Base


class IssueStatus(str, enum.Enum):
    """Statusy zgłoszenia — odpowiadają typowemu workflow."""

    NOWY = "Nowy"
    W_TOKU = "W toku"
    DO_WERYFIKACJI = "Do weryfikacji"
    ZAMKNIETY = "Zamknięty"


class IssuePriority(str, enum.Enum):
    """Priorytety zgłoszenia — od najniższego do krytycznego."""

    NISKI = "Niski"
    SREDNI = "Średni"
    WYSOKI = "Wysoki"
    KRYTYCZNY = "Krytyczny"


class Issue(Base):
    """
    Model zgłoszenia (issue/zadania) w systemie IT Project OS.

    Przechowuje pełne informacje o zadaniu: tytuł, opis, status, priorytet,
    autora, osobę przypisaną oraz znaczniki czasu. Pola author_* i assignee_*
    są opcjonalne — wypełniane danymi z sesji OIDC zalogowanego użytkownika.
    """

    __tablename__ = "issues"
    # Dedykowany schemat PostgreSQL dla modułu Issues — tabele nigdy nie trafiają do public
    __table_args__ = {"schema": "issues"}

    # Klucz główny tabeli
    id = Column(Integer, primary_key=True, index=True)
    # Tytuł zgłoszenia — wymagany, indeksowany dla szybkiego wyszukiwania
    title = Column(String(255), nullable=False, index=True)
    # Szczegółowy opis zadania (opcjonalny)
    description = Column(Text, nullable=True)
    # Status zgłoszenia — wartość domyślna z enum IssueStatus
    status = Column(String(50), nullable=False, default=IssueStatus.NOWY.value, index=True)
    # Priorytet zgłoszenia — wartość domyślna z enum IssuePriority
    priority = Column(String(50), nullable=False, default=IssuePriority.SREDNI.value)
    # Identyfikator autora zgłoszenia (claim `sub` z OIDC)
    author_id = Column(String(255), nullable=True, index=True)
    # Czytelna nazwa autora (preferred_username lub imię i nazwisko)
    author_name = Column(String(255), nullable=True)
    # Identyfikator osoby przypisanej do zgłoszenia (claim `sub` z OIDC)
    assignee_id = Column(String(255), nullable=True, index=True)
    # Czytelna nazwa osoby przypisanej
    assignee_name = Column(String(255), nullable=True)
    # Czas utworzenia zgłoszenia (ustawiany automatycznie przez bazę danych)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    # Czas ostatniej modyfikacji (aktualizowany przez bazę przy każdym UPDATE)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

