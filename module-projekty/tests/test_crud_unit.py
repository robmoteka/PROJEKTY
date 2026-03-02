"""
Testy jednostkowe operacji CRUD (module-projekty/crud.py).

Cel: weryfikacja funkcji crud na sesji SQLAlchemy testowej (SQLite in-memory).
Każda klasa testuje jeden zasób (Server, Project, KPI, Technology, ScopeItem, Port).

Uruchomienie:
    cd module-projekty && pytest tests/test_crud_unit.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

import crud
from models import Project, ProjectKPI, ProjectPort, ProjectScopeItem, ProjectTechnology, Server
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
# Testy CRUD Serwerów
# ---------------------------------------------------------------------------


class TestCreateServer:
    """Weryfikacja funkcji create_server."""

    def test_create_server_returns_server(self, db_session: Session) -> None:
        """create_server powinno zwrócić obiekt Server z przypisanym ID."""
        # Tworzymy serwer z minimalnymi danymi
        server_data = ServerCreate(name="SRV-01", hostname="10.0.0.1")
        result = crud.create_server(db_session, server_data)
        # Sprawdzamy typ i ID
        assert isinstance(result, Server)
        assert result.id > 0

    def test_create_server_sets_defaults(self, db_session: Session) -> None:
        """create_server powinno ustawiać domyślny status 'Aktywny' i typ 'Dev'."""
        server_data = ServerCreate(name="SRV-DEFL", hostname="10.0.0.2")
        result = crud.create_server(db_session, server_data)
        # Domyślne wartości z enum
        assert result.status == "Aktywny"
        assert result.server_type == "Dev"

    def test_create_server_all_fields(self, db_session: Session) -> None:
        """create_server powinno zapisać wszystkie przekazane pola."""
        # Serwer z kompletnym zestawem danych
        server_data = ServerCreate(
            name="PROD-01",
            hostname="172.16.0.1",
            server_type="Prod",
            operating_system="Debian 12",
            description="Serwer produkcyjny",
            status="Aktywny",
        )
        result = crud.create_server(db_session, server_data)
        # Sprawdzamy zapisane pola
        assert result.hostname == "172.16.0.1"
        assert result.operating_system == "Debian 12"
        assert result.description == "Serwer produkcyjny"


class TestGetServers:
    """Weryfikacja funkcji get_servers."""

    def test_get_servers_empty(self, db_session: Session) -> None:
        """get_servers powinno zwrócić pustą listę gdy baza jest pusta."""
        result = crud.get_servers(db_session)
        assert result == []

    def test_get_servers_filter_by_type(self, db_session: Session) -> None:
        """get_servers z filtrem server_type powinno zwrócić tylko pasujące serwery."""
        # Tworzymy serwery różnych typów
        crud.create_server(db_session, ServerCreate(
            name="DEV-01", hostname="10.0.0.1", server_type="Dev"))
        crud.create_server(db_session, ServerCreate(
            name="PROD-01", hostname="10.0.0.2", server_type="Prod"))
        # Filtrujemy tylko serwery DEV
        dev_servers = crud.get_servers(db_session, server_type="Dev")
        assert len(dev_servers) == 1
        assert dev_servers[0].server_type == "Dev"

    def test_get_servers_filter_by_status(self, db_session: Session) -> None:
        """get_servers z filtrem status powinno zwrócić tylko serwery o podanym statusie."""
        # Tworzymy serwery o różnych statusach
        crud.create_server(db_session, ServerCreate(
            name="AKTYWNY", hostname="10.0.1.1", status="Aktywny"))
        crud.create_server(db_session, ServerCreate(
            name="NIEAKTYWNY", hostname="10.0.1.2", status="Nieaktywny"))
        # Filtrujemy tylko aktywne serwery
        active = crud.get_servers(db_session, status="Aktywny")
        assert len(active) == 1
        assert active[0].status == "Aktywny"


class TestUpdateServer:
    """Weryfikacja funkcji update_server."""

    def test_update_server_name(
        self, db_session: Session, sample_server: Server
    ) -> None:
        """update_server powinno zmienić nazwę serwera."""
        # Aktualizujemy nazwę serwera
        update_data = ServerUpdate(name="DEV-UPDATED")
        result = crud.update_server(db_session, sample_server.id, update_data)
        assert result is not None
        assert result.name == "DEV-UPDATED"

    def test_update_nonexistent_returns_none(self, db_session: Session) -> None:
        """update_server dla nieistniejącego ID powinno zwrócić None."""
        update_data = ServerUpdate(name="Ghost Server")
        result = crud.update_server(db_session, 99999, update_data)
        assert result is None


class TestDeleteServer:
    """Weryfikacja funkcji delete_server."""

    def test_delete_existing_server(
        self, db_session: Session, sample_server: Server
    ) -> None:
        """delete_server dla istniejącego serwera powinno zwrócić True."""
        result = crud.delete_server(db_session, sample_server.id)
        assert result is True
        # Sprawdzamy że serwer naprawdę zniknął z bazy
        assert crud.get_server_by_id(db_session, sample_server.id) is None

    def test_delete_nonexistent_server(self, db_session: Session) -> None:
        """delete_server dla nieistniejącego ID powinno zwrócić False."""
        result = crud.delete_server(db_session, 99999)
        assert result is False


# ---------------------------------------------------------------------------
# Testy CRUD Projektów
# ---------------------------------------------------------------------------


class TestCreateProject:
    """Weryfikacja funkcji create_project."""

    def test_create_project_returns_project(self, db_session: Session) -> None:
        """create_project powinno zwrócić obiekt Project z przypisanym ID."""
        project_data = ProjectCreate(name="Projekt Alpha", code="ALPHA-01")
        result = crud.create_project(db_session, project_data)
        # Sprawdzamy typ i ID
        assert isinstance(result, Project)
        assert result.id > 0

    def test_create_project_sets_default_status(self, db_session: Session) -> None:
        """Nowy projekt powinien mieć domyślny status 'Nowy'."""
        project_data = ProjectCreate(name="Projekt Domyślny", code="DEF-01")
        result = crud.create_project(db_session, project_data)
        # Domyślny status z enuma ProjectStatus.NOWY
        assert result.status == "Nowy"

    def test_create_project_stores_all_fields(self, db_session: Session) -> None:
        """create_project powinno zapisać wszystkie przekazane pola."""
        project_data = ProjectCreate(
            name="Pełny Projekt",
            code="FULL-01",
            owner_name="Maria Wiśniewska",
            problem_statement="Optymalizacja procesów",
        )
        result = crud.create_project(db_session, project_data)
        # Sprawdzamy zapisane pola opcjonalne
        assert result.name == "Pełny Projekt"
        assert result.owner_name == "Maria Wiśniewska"
        assert result.problem_statement == "Optymalizacja procesów"

    def test_create_project_with_server_id(
        self, db_session: Session, sample_server: Server
    ) -> None:
        """create_project powinno poprawnie zapisać dev_server_id."""
        project_data = ProjectCreate(
            name="Projekt z Serwerem",
            code="SRVPROJ-01",
            dev_server_id=sample_server.id,
        )
        result = crud.create_project(db_session, project_data)
        assert result.dev_server_id == sample_server.id


class TestGetProjects:
    """Weryfikacja funkcji get_projects."""

    def test_get_projects_empty(self, db_session: Session) -> None:
        """get_projects powinno zwrócić pustą listę gdy baza jest pusta."""
        result = crud.get_projects(db_session)
        assert result == []

    def test_get_projects_returns_all(self, db_session: Session) -> None:
        """get_projects powinno zwrócić wszystkie projekty."""
        # Tworzymy 3 projekty
        for i in range(3):
            crud.create_project(
                db_session, ProjectCreate(name=f"Projekt {i}", code=f"PROJ-{i}")
            )
        result = crud.get_projects(db_session)
        assert len(result) == 3

    def test_get_projects_filter_by_status(self, db_session: Session) -> None:
        """get_projects z filtrem status powinno zwrócić tylko pasujące projekty."""
        # Tworzymy projekty o różnych statusach
        crud.create_project(db_session, ProjectCreate(
            name="Projekt Nowy", code="NEW-01", status="Nowy"))
        crud.create_project(db_session, ProjectCreate(
            name="Projekt W Toku", code="WIP-01", status="W toku"))
        crud.create_project(db_session, ProjectCreate(
            name="Projekt Zamkniety", code="DONE-01", status="Zamknięty"))
        # Filtrujemy tylko projekty o statusie "Nowy"
        new_projects = crud.get_projects(db_session, status="Nowy")
        assert len(new_projects) == 1
        assert new_projects[0].status == "Nowy"

    def test_get_projects_pagination(self, db_session: Session) -> None:
        """get_projects z skip=1 i limit=1 powinno zwrócić dokładnie 1 rekord."""
        # Tworzymy 3 projekty
        for i in range(3):
            crud.create_project(
                db_session, ProjectCreate(name=f"Projekt {i}", code=f"PAGE-{i}")
            )
        # Testujemy paginację — pomijamy 1 i bierzemy tylko 1
        result = crud.get_projects(db_session, skip=1, limit=1)
        assert len(result) == 1


class TestGetProjectById:
    """Weryfikacja funkcji get_project_by_id."""

    def test_get_existing_project(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """get_project_by_id powinno zwrócić projekt dla istniejącego ID."""
        result = crud.get_project_by_id(db_session, sample_project.id)
        assert result is not None
        assert result.id == sample_project.id

    def test_get_nonexistent_project(self, db_session: Session) -> None:
        """get_project_by_id powinno zwrócić None dla nieistniejącego ID."""
        result = crud.get_project_by_id(db_session, 99999)
        assert result is None


class TestGetProjectByCode:
    """Weryfikacja funkcji get_project_by_code."""

    def test_get_existing_by_code(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """get_project_by_code powinno znaleźć projekt po unikalnym kodzie."""
        result = crud.get_project_by_code(db_session, sample_project.code)
        assert result is not None
        assert result.code == sample_project.code

    def test_get_nonexistent_code(self, db_session: Session) -> None:
        """get_project_by_code powinno zwrócić None dla nieistniejącego kodu."""
        result = crud.get_project_by_code(db_session, "NIEISTNIEJACY-99")
        assert result is None


class TestUpdateProject:
    """Weryfikacja funkcji update_project."""

    def test_update_name(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """update_project powinno zmienić nazwę projektu."""
        update_data = ProjectUpdate(name="Zaktualizowana Nazwa")
        result = crud.update_project(db_session, sample_project.id, update_data)
        assert result is not None
        assert result.name == "Zaktualizowana Nazwa"

    def test_update_status(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """update_project powinno zmienić status projektu."""
        update_data = ProjectUpdate(status="W toku")
        result = crud.update_project(db_session, sample_project.id, update_data)
        assert result is not None
        assert result.status == "W toku"

    def test_update_nonexistent(self, db_session: Session) -> None:
        """update_project dla nieistniejącego ID powinno zwrócić None."""
        update_data = ProjectUpdate(name="Duch")
        result = crud.update_project(db_session, 99999, update_data)
        assert result is None


class TestDeleteProject:
    """Weryfikacja funkcji delete_project."""

    def test_delete_existing(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """delete_project dla istniejącego ID powinno zwrócić True."""
        result = crud.delete_project(db_session, sample_project.id)
        assert result is True
        # Sprawdzamy że projekt naprawdę zniknął z bazy
        assert crud.get_project_by_id(db_session, sample_project.id) is None

    def test_delete_nonexistent(self, db_session: Session) -> None:
        """delete_project dla nieistniejącego ID powinno zwrócić False."""
        result = crud.delete_project(db_session, 99999)
        assert result is False

    def test_delete_cascades_children(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """delete_project powinno usunąć kaskadowo KPI, technologie, zakres i porty."""
        project = sample_project_with_children["project"]
        kpi_id = sample_project_with_children["kpi"].id
        tech_id = sample_project_with_children["technology"].id
        scope_id = sample_project_with_children["scope_item"].id
        port_id = sample_project_with_children["port"].id

        # Usuwamy projekt
        crud.delete_project(db_session, project.id)

        # Sprawdzamy że wszystkie encje potomne zostały usunięte
        assert db_session.query(ProjectKPI).filter_by(id=kpi_id).first() is None
        assert db_session.query(ProjectTechnology).filter_by(id=tech_id).first() is None
        assert db_session.query(ProjectScopeItem).filter_by(id=scope_id).first() is None
        assert db_session.query(ProjectPort).filter_by(id=port_id).first() is None


# ---------------------------------------------------------------------------
# Testy CRUD KPI
# ---------------------------------------------------------------------------


class TestCRUDKPI:
    """Weryfikacja funkcji CRUD dla wskaźników KPI projektu."""

    def test_create_kpi(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """create_kpi powinno zwrócić obiekt ProjectKPI z przypisanym ID."""
        kpi_data = KPICreate(
            name="Czas odpowiedzi", target_value="< 200ms", unit="ms"
        )
        result = crud.create_kpi(db_session, sample_project.id, kpi_data)
        assert isinstance(result, ProjectKPI)
        assert result.id > 0
        assert result.project_id == sample_project.id

    def test_get_kpi_by_id(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """get_kpi_by_id powinno zwrócić KPI dla istniejącego ID."""
        kpi_id = sample_project_with_children["kpi"].id
        result = crud.get_kpi_by_id(db_session, kpi_id)
        assert result is not None
        assert result.id == kpi_id

    def test_update_kpi(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """update_kpi powinno zmienić pola KPI."""
        kpi_id = sample_project_with_children["kpi"].id
        update_data = KPIUpdate(current_value="150ms")
        result = crud.update_kpi(db_session, kpi_id, update_data)
        assert result is not None
        assert result.current_value == "150ms"

    def test_delete_kpi(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """delete_kpi powinno zwrócić True i usunąć KPI z bazy."""
        kpi_id = sample_project_with_children["kpi"].id
        result = crud.delete_kpi(db_session, kpi_id)
        assert result is True
        # Weryfikujemy brak KPI w bazie
        assert crud.get_kpi_by_id(db_session, kpi_id) is None


# ---------------------------------------------------------------------------
# Testy CRUD Technologii
# ---------------------------------------------------------------------------


class TestCRUDTechnology:
    """Weryfikacja funkcji CRUD dla technologii projektu."""

    def test_create_technology(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """create_technology powinno zwrócić obiekt ProjectTechnology z ID."""
        tech_data = TechnologyCreate(
            category="Backend", name="FastAPI", version="≥ 0.110.0"
        )
        result = crud.create_technology(db_session, sample_project.id, tech_data)
        assert isinstance(result, ProjectTechnology)
        assert result.id > 0
        assert result.project_id == sample_project.id

    def test_get_technology_by_id(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """get_technology_by_id powinno zwrócić technologię dla istniejącego ID."""
        tech_id = sample_project_with_children["technology"].id
        result = crud.get_technology_by_id(db_session, tech_id)
        assert result is not None
        assert result.id == tech_id

    def test_update_technology(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """update_technology powinno zmienić pola technologii."""
        tech_id = sample_project_with_children["technology"].id
        update_data = TechnologyUpdate(version="≥ 0.115.0")
        result = crud.update_technology(db_session, tech_id, update_data)
        assert result is not None
        assert result.version == "≥ 0.115.0"

    def test_delete_technology(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """delete_technology powinno zwrócić True i usunąć technologię z bazy."""
        tech_id = sample_project_with_children["technology"].id
        result = crud.delete_technology(db_session, tech_id)
        assert result is True
        # Weryfikujemy brak technologii w bazie
        assert crud.get_technology_by_id(db_session, tech_id) is None


# ---------------------------------------------------------------------------
# Testy CRUD elementów zakresu
# ---------------------------------------------------------------------------


class TestCRUDScopeItem:
    """Weryfikacja funkcji CRUD dla elementów zakresu projektu."""

    def test_create_scope_item(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """create_scope_item powinno zwrócić obiekt ProjectScopeItem z ID."""
        item_data = ScopeItemCreate(
            category="Must-have", description="Uwierzytelnianie użytkowników"
        )
        result = crud.create_scope_item(db_session, sample_project.id, item_data)
        assert isinstance(result, ProjectScopeItem)
        assert result.id > 0
        assert result.project_id == sample_project.id

    def test_get_scope_item_by_id(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """get_scope_item_by_id powinno zwrócić element zakresu dla istniejącego ID."""
        scope_id = sample_project_with_children["scope_item"].id
        result = crud.get_scope_item_by_id(db_session, scope_id)
        assert result is not None
        assert result.id == scope_id

    def test_update_scope_item(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """update_scope_item powinno zmienić pola elementu zakresu."""
        scope_id = sample_project_with_children["scope_item"].id
        update_data = ScopeItemUpdate(priority=1)
        result = crud.update_scope_item(db_session, scope_id, update_data)
        assert result is not None
        assert result.priority == 1

    def test_delete_scope_item(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """delete_scope_item powinno zwrócić True i usunąć element z bazy."""
        scope_id = sample_project_with_children["scope_item"].id
        result = crud.delete_scope_item(db_session, scope_id)
        assert result is True
        # Weryfikujemy brak elementu w bazie
        assert crud.get_scope_item_by_id(db_session, scope_id) is None


# ---------------------------------------------------------------------------
# Testy CRUD portów
# ---------------------------------------------------------------------------


class TestCRUDPort:
    """Weryfikacja funkcji CRUD dla portów sieciowych projektu."""

    def test_create_port(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """create_port powinno zwrócić obiekt ProjectPort z ID."""
        port_data = PortCreate(
            port_number=8080, protocol="TCP", service_name="API"
        )
        result = crud.create_port(db_session, sample_project.id, port_data)
        assert isinstance(result, ProjectPort)
        assert result.id > 0
        assert result.project_id == sample_project.id
        assert result.port_number == 8080

    def test_get_port_by_id(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """get_port_by_id powinno zwrócić port dla istniejącego ID."""
        port_id = sample_project_with_children["port"].id
        result = crud.get_port_by_id(db_session, port_id)
        assert result is not None
        assert result.id == port_id

    def test_get_project_ports(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """get_project_ports powinno zwrócić listę portów przypisanych do projektu."""
        project_id = sample_project_with_children["project"].id
        result = crud.get_project_ports(db_session, project_id)
        # Fixture tworzy jeden port — powinien być na liście
        assert len(result) >= 1
        assert all(p.project_id == project_id for p in result)

    def test_update_port(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """update_port powinno zmienić pola portu."""
        port_id = sample_project_with_children["port"].id
        update_data = PortUpdate(service_name="API Gateway")
        result = crud.update_port(db_session, port_id, update_data)
        assert result is not None
        assert result.service_name == "API Gateway"

    def test_delete_port(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """delete_port powinno zwrócić True i usunąć port z bazy."""
        port_id = sample_project_with_children["port"].id
        result = crud.delete_port(db_session, port_id)
        assert result is True
        # Weryfikujemy brak portu w bazie
        assert crud.get_port_by_id(db_session, port_id) is None
