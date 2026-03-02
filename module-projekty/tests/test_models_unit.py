"""
Testy jednostkowe modeli SQLAlchemy (module-projekty/models.py).

Cel: weryfikacja wartości enumów, domyślnych kolumn, struktury tabel i cascade delete.
Baza danych: SQLite in-memory (fixture z conftest.py).

Uruchomienie:
    cd module-projekty && pytest tests/test_models_unit.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import (
    PortProtocol,
    Project,
    ProjectKPI,
    ProjectPort,
    ProjectScopeItem,
    ProjectStatus,
    ProjectTechnology,
    ScopeCategory,
    Server,
    ServerStatus,
    ServerType,
    TechnologyCategory,
)


# ---------------------------------------------------------------------------
# Testy enumu ProjectStatus
# ---------------------------------------------------------------------------


class TestProjectStatusEnum:
    """Weryfikacja że enum ProjectStatus ma poprawne wartości string."""

    def test_status_nowy_ma_poprawna_wartosc(self) -> None:
        """ProjectStatus.NOWY powinno mieć wartość 'Nowy'."""
        assert ProjectStatus.NOWY.value == "Nowy"

    def test_status_w_toku_ma_poprawna_wartosc(self) -> None:
        """ProjectStatus.W_TOKU powinno mieć wartość 'W toku'."""
        assert ProjectStatus.W_TOKU.value == "W toku"

    def test_status_wstrzymany_ma_poprawna_wartosc(self) -> None:
        """ProjectStatus.WSTRZYMANY powinno mieć wartość 'Wstrzymany'."""
        assert ProjectStatus.WSTRZYMANY.value == "Wstrzymany"

    def test_status_zamkniety_ma_poprawna_wartosc(self) -> None:
        """ProjectStatus.ZAMKNIETY powinno mieć wartość 'Zamknięty'."""
        assert ProjectStatus.ZAMKNIETY.value == "Zamknięty"

    def test_status_anulowany_ma_poprawna_wartosc(self) -> None:
        """ProjectStatus.ANULOWANY powinno mieć wartość 'Anulowany'."""
        assert ProjectStatus.ANULOWANY.value == "Anulowany"

    def test_enum_jest_podtypem_str(self) -> None:
        """ProjectStatus powinno dziedziczyć po str — umożliwia bezposrednie porównanie."""
        assert isinstance(ProjectStatus.NOWY, str)
        assert ProjectStatus.NOWY == "Nowy"


# ---------------------------------------------------------------------------
# Testy enumu TechnologyCategory
# ---------------------------------------------------------------------------


class TestTechnologyCategoryEnum:
    """Weryfikacja że enum TechnologyCategory ma poprawne wartości string."""

    def test_frontend_ma_poprawna_wartosc(self) -> None:
        """TechnologyCategory.FRONTEND powinno mieć wartość 'Frontend'."""
        assert TechnologyCategory.FRONTEND.value == "Frontend"

    def test_backend_ma_poprawna_wartosc(self) -> None:
        """TechnologyCategory.BACKEND powinno mieć wartość 'Backend'."""
        assert TechnologyCategory.BACKEND.value == "Backend"

    def test_baza_danych_ma_poprawna_wartosc(self) -> None:
        """TechnologyCategory.BAZA_DANYCH powinno mieć wartość 'Baza danych'."""
        assert TechnologyCategory.BAZA_DANYCH.value == "Baza danych"

    def test_infrastruktura_ma_poprawna_wartosc(self) -> None:
        """TechnologyCategory.INFRASTRUKTURA powinno mieć wartość 'Infrastruktura'."""
        assert TechnologyCategory.INFRASTRUKTURA.value == "Infrastruktura"

    def test_integracje_ma_poprawna_wartosc(self) -> None:
        """TechnologyCategory.INTEGRACJE powinno mieć wartość 'Integracje'."""
        assert TechnologyCategory.INTEGRACJE.value == "Integracje"


# ---------------------------------------------------------------------------
# Testy enumu ScopeCategory
# ---------------------------------------------------------------------------


class TestScopeCategoryEnum:
    """Weryfikacja że enum ScopeCategory ma poprawne wartości string."""

    def test_must_have_ma_poprawna_wartosc(self) -> None:
        """ScopeCategory.MUST_HAVE powinno mieć wartość 'Must-have'."""
        assert ScopeCategory.MUST_HAVE.value == "Must-have"

    def test_out_of_scope_ma_poprawna_wartosc(self) -> None:
        """ScopeCategory.OUT_OF_SCOPE powinno mieć wartość 'Out of scope'."""
        assert ScopeCategory.OUT_OF_SCOPE.value == "Out of scope"

    def test_niefunkcjonalne_ma_poprawna_wartosc(self) -> None:
        """ScopeCategory.NIEFUNKCJONALNE powinno mieć wartość 'Niefunkcjonalne'."""
        assert ScopeCategory.NIEFUNKCJONALNE.value == "Niefunkcjonalne"


# ---------------------------------------------------------------------------
# Testy enumu ServerType
# ---------------------------------------------------------------------------


class TestServerTypeEnum:
    """Weryfikacja że enum ServerType ma poprawne wartości string."""

    def test_dev_ma_poprawna_wartosc(self) -> None:
        """ServerType.DEV powinno mieć wartość 'Dev'."""
        assert ServerType.DEV.value == "Dev"

    def test_staging_ma_poprawna_wartosc(self) -> None:
        """ServerType.STAGING powinno mieć wartość 'Staging'."""
        assert ServerType.STAGING.value == "Staging"

    def test_prod_ma_poprawna_wartosc(self) -> None:
        """ServerType.PROD powinno mieć wartość 'Prod'."""
        assert ServerType.PROD.value == "Prod"

    def test_shared_ma_poprawna_wartosc(self) -> None:
        """ServerType.SHARED powinno mieć wartość 'Shared'."""
        assert ServerType.SHARED.value == "Shared"


# ---------------------------------------------------------------------------
# Testy enumu ServerStatus
# ---------------------------------------------------------------------------


class TestServerStatusEnum:
    """Weryfikacja że enum ServerStatus ma poprawne wartości string."""

    def test_aktywny_ma_poprawna_wartosc(self) -> None:
        """ServerStatus.AKTYWNY powinno mieć wartość 'Aktywny'."""
        assert ServerStatus.AKTYWNY.value == "Aktywny"

    def test_nieaktywny_ma_poprawna_wartosc(self) -> None:
        """ServerStatus.NIEAKTYWNY powinno mieć wartość 'Nieaktywny'."""
        assert ServerStatus.NIEAKTYWNY.value == "Nieaktywny"


# ---------------------------------------------------------------------------
# Testy enumu PortProtocol
# ---------------------------------------------------------------------------


class TestPortProtocolEnum:
    """Weryfikacja że enum PortProtocol ma poprawne wartości string."""

    def test_tcp_ma_poprawna_wartosc(self) -> None:
        """PortProtocol.TCP powinno mieć wartość 'TCP'."""
        assert PortProtocol.TCP.value == "TCP"

    def test_udp_ma_poprawna_wartosc(self) -> None:
        """PortProtocol.UDP powinno mieć wartość 'UDP'."""
        assert PortProtocol.UDP.value == "UDP"

    def test_tcp_udp_ma_poprawna_wartosc(self) -> None:
        """PortProtocol.TCP_UDP powinno mieć wartość 'TCP/UDP'."""
        assert PortProtocol.TCP_UDP.value == "TCP/UDP"


# ---------------------------------------------------------------------------
# Testy modelu Server
# ---------------------------------------------------------------------------


class TestServerModel:
    """Weryfikacja struktury i domyślnych wartości modelu Server."""

    def test_create_server_with_defaults(self, db_session: Session) -> None:
        """Nowy serwer powinien mieć domyślny status 'Aktywny' i typ 'Dev'."""
        # Tworzymy serwer bez podawania opcjonalnych pól
        server = Server(name="SRV-01", hostname="10.0.0.1")
        db_session.add(server)
        db_session.commit()
        db_session.refresh(server)
        # Domyślne wartości z definicji modelu
        assert server.status == ServerStatus.AKTYWNY.value
        assert server.server_type == ServerType.DEV.value

    def test_server_name_not_nullable(self, db_session: Session) -> None:
        """Próba zapisania serwera bez nazwy powinna rzucić IntegrityError."""
        # Celowo pomijamy wymagane pole name
        server = Server(hostname="10.0.0.2")
        db_session.add(server)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_server_hostname_not_nullable(self, db_session: Session) -> None:
        """Próba zapisania serwera bez hostname powinna rzucić IntegrityError."""
        # Celowo pomijamy wymagane pole hostname
        server = Server(name="SRV-NOHOSTNAME")
        db_session.add(server)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_server_table_name_is_servers(self) -> None:
        """Tabela serwera powinna mieć nazwę 'servers'."""
        assert Server.__tablename__ == "servers"

    def test_server_schema_is_projekty(self) -> None:
        """Tabela serwera powinna należeć do schematu 'projekty'."""
        assert Server.__table_args__["schema"] == "projekty"


# ---------------------------------------------------------------------------
# Testy modelu Project
# ---------------------------------------------------------------------------


class TestProjectModel:
    """Weryfikacja struktury i domyślnych wartości modelu Project."""

    def test_create_project_with_defaults(self, db_session: Session) -> None:
        """Nowy projekt powinien mieć domyślny status 'Nowy'."""
        # Tworzymy projekt z minimalnymi wymaganymi polami
        project = Project(name="Projekt Alpha", code="ALPHA-01")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        # Domyślny status zdefiniowany w modelu
        assert project.status == ProjectStatus.NOWY.value

    def test_project_name_not_nullable(self, db_session: Session) -> None:
        """Próba zapisania projektu bez nazwy powinna rzucić IntegrityError."""
        project = Project(code="NONAME-01")
        db_session.add(project)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_project_code_not_nullable(self, db_session: Session) -> None:
        """Próba zapisania projektu bez kodu powinna rzucić IntegrityError."""
        project = Project(name="Projekt Bez Kodu")
        db_session.add(project)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_project_code_unique(self, db_session: Session) -> None:
        """Dwa projekty z identycznym kodem powinny rzucić IntegrityError."""
        # Tworzymy pierwszy projekt
        project_a = Project(name="Projekt A", code="DUPLIKAT")
        db_session.add(project_a)
        db_session.commit()
        # Próbujemy dodać drugi projekt z tym samym kodem
        project_b = Project(name="Projekt B", code="DUPLIKAT")
        db_session.add(project_b)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_project_nullable_fields(self, db_session: Session) -> None:
        """Opcjonalne pola owner_name, start_date, end_date mogą być None."""
        # Tworzymy projekt z tylko wymaganymi polami
        project = Project(name="Projekt Minimalny", code="MIN-01")
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        # Opcjonalne pola powinny być None
        assert project.owner_name is None
        assert project.start_date is None
        assert project.end_date is None

    def test_project_dev_server_relationship(
        self, db_session: Session, sample_server: Server
    ) -> None:
        """Projekt powinien mieć dostęp do powiązanego serwera DEV przez relację."""
        # Tworzymy projekt powiązany z serwerem testowym
        project = Project(
            name="Projekt z Serwerem",
            code="SRV-PROJ-01",
            dev_server_id=sample_server.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        # Relacja powinna wskazywać na właściwy serwer
        assert project.dev_server is not None
        assert project.dev_server.id == sample_server.id

    def test_project_table_name_is_projects(self) -> None:
        """Tabela projektu powinna mieć nazwę 'projects'."""
        assert Project.__tablename__ == "projects"

    def test_project_schema_is_projekty(self) -> None:
        """Tabela projektu powinna należeć do schematu 'projekty'."""
        assert Project.__table_args__["schema"] == "projekty"


# ---------------------------------------------------------------------------
# Testy modelu ProjectKPI
# ---------------------------------------------------------------------------


class TestProjectKPIModel:
    """Weryfikacja struktury modelu ProjectKPI i jego powiązania z projektem."""

    def test_create_kpi_linked_to_project(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """KPI powinno mieć poprawne project_id powiązane z projektem nadrzędnym."""
        # Tworzymy KPI przypisane do projektu testowego
        kpi = ProjectKPI(
            project_id=sample_project.id,
            name="Dostępność systemu",
            target_value="99.9%",
        )
        db_session.add(kpi)
        db_session.commit()
        db_session.refresh(kpi)
        # Sprawdzamy powiązanie FK
        assert kpi.project_id == sample_project.id

    def test_kpi_name_not_nullable(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """KPI bez nazwy powinno rzucić IntegrityError."""
        # Celowo pomijamy wymagane pole name
        kpi = ProjectKPI(
            project_id=sample_project.id,
            target_value="100%",
        )
        db_session.add(kpi)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_kpi_target_value_not_nullable(
        self, db_session: Session, sample_project: Project
    ) -> None:
        """KPI bez target_value powinno rzucić IntegrityError."""
        # Celowo pomijamy wymagane pole target_value
        kpi = ProjectKPI(
            project_id=sample_project.id,
            name="KPI bez wartości docelowej",
        )
        db_session.add(kpi)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


# ---------------------------------------------------------------------------
# Testy kaskadowego usuwania
# ---------------------------------------------------------------------------


class TestCascadeDelete:
    """Weryfikacja że usunięcie projektu kasuje wszystkie powiązane encje potomne."""

    def test_delete_project_cascades_kpis(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """Usunięcie projektu powinno automatycznie usunąć wszystkie jego KPI."""
        project = sample_project_with_children["project"]
        kpi_id = sample_project_with_children["kpi"].id

        # Usuwamy projekt — cascade powinno usunąć powiązane KPI
        db_session.delete(project)
        db_session.commit()

        # Sprawdzamy że KPI zostało usunięte
        deleted_kpi = db_session.query(ProjectKPI).filter_by(id=kpi_id).first()
        assert deleted_kpi is None

    def test_delete_project_cascades_technologies(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """Usunięcie projektu powinno automatycznie usunąć wszystkie jego technologie."""
        project = sample_project_with_children["project"]
        tech_id = sample_project_with_children["technology"].id

        # Usuwamy projekt — cascade powinno usunąć powiązane technologie
        db_session.delete(project)
        db_session.commit()

        # Sprawdzamy że technologia została usunięta
        deleted_tech = db_session.query(ProjectTechnology).filter_by(id=tech_id).first()
        assert deleted_tech is None

    def test_delete_project_cascades_ports(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """Usunięcie projektu powinno automatycznie usunąć wszystkie jego porty."""
        project = sample_project_with_children["project"]
        port_id = sample_project_with_children["port"].id

        # Usuwamy projekt — cascade powinno usunąć powiązane porty
        db_session.delete(project)
        db_session.commit()

        # Sprawdzamy że port został usunięty
        deleted_port = db_session.query(ProjectPort).filter_by(id=port_id).first()
        assert deleted_port is None

    def test_delete_project_cascades_scope_items(
        self, db_session: Session, sample_project_with_children: dict
    ) -> None:
        """Usunięcie projektu powinno automatycznie usunąć wszystkie elementy zakresu."""
        project = sample_project_with_children["project"]
        scope_id = sample_project_with_children["scope_item"].id

        # Usuwamy projekt — cascade powinno usunąć powiązane elementy zakresu
        db_session.delete(project)
        db_session.commit()

        # Sprawdzamy że element zakresu został usunięty
        deleted_scope = db_session.query(ProjectScopeItem).filter_by(id=scope_id).first()
        assert deleted_scope is None
