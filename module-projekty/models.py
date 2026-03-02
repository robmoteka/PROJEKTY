"""
Modele ORM dla modułu Projekty — definicje tabel w schemacie 'projekty'.

Zawiera 6 enumeracji i 6 modeli SQLAlchemy reprezentujących:
- Serwery infrastrukturalne (Server)
- Projekty IT (Project)
- Wskaźniki sukcesu projektów (ProjectKPI)
- Technologie stosowane w projektach (ProjectTechnology)
- Elementy zakresu projektów (ProjectScopeItem)
- Porty sieciowe przypisane do projektów (ProjectPort)
"""

from __future__ import annotations

import enum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


# ---------------------------------------------------------------------------
# Enumeracje — wartości słownikowe dla kolumn tekstowych
# ---------------------------------------------------------------------------


class ProjectStatus(str, enum.Enum):
    """Statusy projektu — cykl życia od nowego do zamkniętego."""

    NOWY = "Nowy"
    W_TOKU = "W toku"
    WSTRZYMANY = "Wstrzymany"
    ZAMKNIETY = "Zamknięty"
    ANULOWANY = "Anulowany"


class TechnologyCategory(str, enum.Enum):
    """Kategorie technologii w stosie projektu."""

    FRONTEND = "Frontend"
    BACKEND = "Backend"
    BAZA_DANYCH = "Baza danych"
    INFRASTRUKTURA = "Infrastruktura"
    INTEGRACJE = "Integracje"


class ScopeCategory(str, enum.Enum):
    """Kategorie elementów zakresu projektu."""

    MUST_HAVE = "Must-have"
    OUT_OF_SCOPE = "Out of scope"
    NIEFUNKCJONALNE = "Niefunkcjonalne"


class ServerType(str, enum.Enum):
    """Typ środowiska serwera."""

    DEV = "Dev"
    STAGING = "Staging"
    PROD = "Prod"
    SHARED = "Shared"


class ServerStatus(str, enum.Enum):
    """Status aktywności serwera."""

    AKTYWNY = "Aktywny"
    NIEAKTYWNY = "Nieaktywny"


class PortProtocol(str, enum.Enum):
    """Protokół portu sieciowego."""

    TCP = "TCP"
    UDP = "UDP"
    TCP_UDP = "TCP/UDP"


# ---------------------------------------------------------------------------
# Modele ORM — tabele w schemacie 'projekty'
# ---------------------------------------------------------------------------


class Server(Base):
    """
    Model serwera infrastrukturalnego.

    Przechowuje informacje o maszynach (Dev/Staging/Prod/Shared),
    z których korzystają projekty w systemie.
    """

    __tablename__ = "servers"
    __table_args__ = {"schema": "projekty"}

    # Klucz główny — auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Unikalna nazwa serwera, np. "DEV-01"
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Adres IP lub hostname serwera
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    # Typ środowiska — wartość z enum ServerType
    server_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ServerType.DEV.value
    )
    # System operacyjny, np. "Ubuntu 22.04"
    operating_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Opis i notatki dotyczące serwera
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Status aktywności — wartość z enum ServerStatus
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ServerStatus.AKTYWNY.value
    )
    # Timestamp tworzenia rekordu — generowany przez bazę danych
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # Timestamp ostatniej aktualizacji — automatycznie odświeżany
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Project(Base):
    """
    Model projektu IT.

    Centralny model systemu — powiązany z serwerami infrastrukturalnymi
    oraz dziećmi (KPI, technologie, zakres, porty) usuwanym kaskadowo.
    """

    __tablename__ = "projects"
    __table_args__ = {"schema": "projekty"}

    # Klucz główny — auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Nazwa projektu
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Unikalny kod projektu, np. "PROJECT-X-2026"
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    # Status projektu z cyklu życia — wartość z enum ProjectStatus
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProjectStatus.NOWY.value, index=True
    )
    # Imię właściciela (Product Owner)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # ID właściciela z claims OIDC — powiązanie z dostawcą tożsamości
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    # Cel biznesowy / Problem Statement projektu
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Planowana data rozpoczęcia projektu
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    # Planowana data zakończenia projektu
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    # FK do serwera deweloperskiego — zerowane przy usunięciu serwera
    dev_server_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("projekty.servers.id", ondelete="SET NULL"),
        nullable=True,
    )
    # FK do serwera produkcyjnego — zerowane przy usunięciu serwera
    prod_server_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("projekty.servers.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Początek zakresu portów przypisanych do projektu
    port_range_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Koniec zakresu portów przypisanych do projektu
    port_range_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Timestamp tworzenia rekordu — generowany przez bazę danych
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # Timestamp ostatniej aktualizacji — automatycznie odświeżany
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Serwer deweloperski — opcjonalne powiązanie
    dev_server: Mapped[Server | None] = relationship(
        "Server", foreign_keys=[dev_server_id]
    )
    # Serwer produkcyjny — opcjonalne powiązanie
    prod_server: Mapped[Server | None] = relationship(
        "Server", foreign_keys=[prod_server_id]
    )
    # Kluczowe wskaźniki sukcesu — kaskadowe usunięcie wraz z projektem
    kpis: Mapped[list[ProjectKPI]] = relationship(
        "ProjectKPI", back_populates="project", cascade="all, delete-orphan"
    )
    # Technologie w stosie — kaskadowe usunięcie wraz z projektem
    technologies: Mapped[list[ProjectTechnology]] = relationship(
        "ProjectTechnology", back_populates="project", cascade="all, delete-orphan"
    )
    # Elementy zakresu — kaskadowe usunięcie wraz z projektem
    scope_items: Mapped[list[ProjectScopeItem]] = relationship(
        "ProjectScopeItem", back_populates="project", cascade="all, delete-orphan"
    )
    # Przypisane porty — kaskadowe usunięcie wraz z projektem
    ports: Mapped[list[ProjectPort]] = relationship(
        "ProjectPort", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectKPI(Base):
    """
    Model wskaźnika kluczowego sukcesu (KPI) projektu.

    Przechowuje mierzalne cele do osiągnięcia w ramach projektu,
    np. "Czas przetwarzania danych < 30s".
    """

    __tablename__ = "project_kpis"
    __table_args__ = {"schema": "projekty"}

    # Klucz główny — auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # FK do projektu nadrzędnego — wymagane
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projekty.projects.id"), nullable=False
    )
    # Nazwa wskaźnika, np. "Czas przetwarzania danych"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Docelowa wartość wskaźnika, np. "< 30s"
    target_value: Mapped[str] = mapped_column(String(255), nullable=False)
    # Aktualna wartość wskaźnika — aktualizowana w miarę postępów
    current_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Jednostka miary, np. "sekundy", "%"
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Projekt nadrzędny — odwrotna strona relacji
    project: Mapped[Project] = relationship("Project", back_populates="kpis")


class ProjectTechnology(Base):
    """
    Model technologii stosowanej w projekcie.

    Reprezentuje pojedynczy element stosu technologicznego,
    np. "FastAPI ≥ 0.110.0" w kategorii Backend.
    """

    __tablename__ = "project_technologies"
    __table_args__ = {"schema": "projekty"}

    # Klucz główny — auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # FK do projektu nadrzędnego — wymagane
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projekty.projects.id"), nullable=False
    )
    # Kategoria technologii — wartość z enum TechnologyCategory
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TechnologyCategory.BACKEND.value
    )
    # Nazwa technologii, np. "FastAPI"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Wersja technologii, np. "≥ 0.110.0"
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Opis roli technologii w projekcie
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Projekt nadrzędny — odwrotna strona relacji
    project: Mapped[Project] = relationship("Project", back_populates="technologies")


class ProjectScopeItem(Base):
    """
    Model elementu zakresu projektu.

    Kategoryzuje wymagania jako Must-have, Out of scope
    lub Niefunkcjonalne z opcjonalnym priorytetem.
    """

    __tablename__ = "project_scope_items"
    __table_args__ = {"schema": "projekty"}

    # Klucz główny — auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # FK do projektu nadrzędnego — wymagane
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projekty.projects.id"), nullable=False
    )
    # Kategoria zakresu — wartość z enum ScopeCategory
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # Opis elementu zakresu
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Priorytet/kolejność wyświetlania — opcjonalny
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Projekt nadrzędny — odwrotna strona relacji
    project: Mapped[Project] = relationship("Project", back_populates="scope_items")


class ProjectPort(Base):
    """
    Model portu sieciowego przypisanego do projektu.

    Przechowuje informacje o portach używanych przez usługi projektu,
    np. port 8000/TCP dla API FastAPI.
    """

    __tablename__ = "project_ports"
    __table_args__ = {"schema": "projekty"}

    # Klucz główny — auto-increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # FK do projektu nadrzędnego — wymagane
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projekty.projects.id"), nullable=False
    )
    # Numer portu sieciowego
    port_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Protokół portu — wartość z enum PortProtocol
    protocol: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PortProtocol.TCP.value
    )
    # Nazwa usługi korzystającej z portu, np. "Nginx", "API"
    service_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Opis przeznaczenia portu
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Projekt nadrzędny — odwrotna strona relacji
    project: Mapped[Project] = relationship("Project", back_populates="ports")
