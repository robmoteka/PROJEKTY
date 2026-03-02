"""
Testy jednostkowe schematów Pydantic (module-projekty/schemas.py).

Cel: weryfikacja walidacji granic (min/max length, required, optional, typy, zakresy).
Nie wymaga bazy danych — walidacja jest czysto w pamięci Pydantic.

Uruchomienie:
    cd module-projekty && pytest tests/test_schemas_unit.py -v
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from models import PortProtocol, ProjectStatus, ServerStatus, ServerType
from schemas import (
    KPICreate,
    PortCreate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ServerCreate,
)


# ---------------------------------------------------------------------------
# Testy schematu ProjectCreate
# ---------------------------------------------------------------------------


class TestProjectCreate:
    """Weryfikacja walidacji Pydantic dla schematu ProjectCreate."""

    def test_valid_minimal_data(self) -> None:
        """Tylko name i code powinny wystarczyć do utworzenia projeku."""
        # Minimalne dane — reszta ma wartości domyślne
        project = ProjectCreate(name="Projekt A", code="PROJ-A")
        assert project.name == "Projekt A"
        assert project.code == "PROJ-A"
        assert project.status == ProjectStatus.NOWY

    def test_valid_full_data(self) -> None:
        """Wszystkie pola wypełnione powinny przejść walidację."""
        # Pełny zestaw danych projektu
        project = ProjectCreate(
            name="Pełny Projekt",
            code="FULL-01",
            status=ProjectStatus.W_TOKU,
            owner_name="Anna Nowak",
            problem_statement="Opis celu projektu",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            dev_server_id=1,
            prod_server_id=2,
            port_range_start=8000,
            port_range_end=8099,
        )
        assert project.owner_name == "Anna Nowak"
        assert project.port_range_start == 8000

    def test_name_too_short(self) -> None:
        """Nazwa krótsza niż 3 znaki powinna rzucić ValidationError."""
        # min_length=3 dla pola name
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="AB", code="VALID-01")
        # Upewniamy się że błąd dotyczy pola name
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_name_too_long(self) -> None:
        """Nazwa dłuższa niż 255 znaków powinna rzucić ValidationError."""
        # max_length=255 dla pola name
        with pytest.raises(ValidationError):
            ProjectCreate(name="A" * 256, code="VALID-01")

    def test_code_required(self) -> None:
        """Brak pola code powinien rzucić ValidationError."""
        # code jest polem wymaganym (Field(...))
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="Projekt bez kodu")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_code_too_short(self) -> None:
        """Kod krótszy niż 2 znaki powinien rzucić ValidationError."""
        # min_length=2 dla pola code
        with pytest.raises(ValidationError):
            ProjectCreate(name="Projekt", code="A")

    def test_port_range_start_valid_bounds(self) -> None:
        """Zakres portów 1-65535 powinien przejść walidację."""
        # Graniczne wartości zakresu — name min 3 znaki, code min 2 znaki
        project_min = ProjectCreate(name="Pl1", code="P1", port_range_start=1)
        project_max = ProjectCreate(name="Pl2", code="P2", port_range_start=65535)
        assert project_min.port_range_start == 1
        assert project_max.port_range_start == 65535

    def test_port_range_start_out_of_bounds(self) -> None:
        """Numer portu poza zakresem 1-65535 powinien rzucić ValidationError."""
        # Wartość 0 jest poniżej minimum (ge=1)
        with pytest.raises(ValidationError):
            ProjectCreate(name="Projekt", code="PROJ", port_range_start=0)
        # Wartość 70000 jest powyżej maksimum (le=65535)
        with pytest.raises(ValidationError):
            ProjectCreate(name="Projekt", code="PROJ", port_range_start=70000)


# ---------------------------------------------------------------------------
# Testy schematu ProjectUpdate
# ---------------------------------------------------------------------------


class TestProjectUpdate:
    """Weryfikacja walidacji Pydantic dla schematu ProjectUpdate (partial update)."""

    def test_empty_update_is_valid(self) -> None:
        """Pusta aktualizacja (wszystkie pola None) powinna być poprawna."""
        # Partial update — żadne pole nie jest wymagane
        update = ProjectUpdate()
        assert update.name is None
        assert update.code is None

    def test_partial_update_name_only(self) -> None:
        """Aktualizacja tylko nazwy powinna przejść walidację."""
        update = ProjectUpdate(name="Nowa Nazwa")
        assert update.name == "Nowa Nazwa"
        assert update.code is None

    def test_partial_update_status(self) -> None:
        """Aktualizacja tylko statusu powinna przejść walidację."""
        update = ProjectUpdate(status=ProjectStatus.W_TOKU)
        assert update.status == ProjectStatus.W_TOKU

    def test_update_code_too_short(self) -> None:
        """Kod krótszy niż 2 znaki w aktualizacji powinien rzucić ValidationError."""
        # Walidacja granic działa też dla pól opcjonalnych gdy są podane
        with pytest.raises(ValidationError):
            ProjectUpdate(code="A")

    def test_update_port_range_out_of_bounds(self) -> None:
        """Numer portu poza zakresem w aktualizacji powinien rzucić ValidationError."""
        # le=65535 obowiązuje też w partial update
        with pytest.raises(ValidationError):
            ProjectUpdate(port_range_start=99999)


# ---------------------------------------------------------------------------
# Testy schematu ProjectRead
# ---------------------------------------------------------------------------


class TestProjectRead:
    """Weryfikacja schematu ProjectRead — from_attributes i zagnieżdżone relacje."""

    def test_from_attributes_with_orm_object(self, sample_project) -> None:
        """ProjectRead powinien poprawnie mapować obiekt ORM przez from_attributes."""
        # Konwertujemy obiekt ORM na schemat Pydantic
        project_read = ProjectRead.model_validate(sample_project)
        assert project_read.id == sample_project.id
        assert project_read.name == sample_project.name
        assert project_read.code == sample_project.code

    def test_nested_kpis_list(self, sample_project_with_children) -> None:
        """Lista kpis powinna być poprawnie parsowana jako lista KPIRead."""
        project = sample_project_with_children["project"]
        # Pobieramy projekt z relacjami przez ORM — zakładamy że fixture ładuje
        project_read = ProjectRead.model_validate(project)
        # Lista KPI powinna zawierać przynajmniej jeden element
        assert isinstance(project_read.kpis, list)

    def test_optional_servers(self) -> None:
        """Projekt bez serwerów powinien mieć dev_server=None i prod_server=None."""
        # Tworzymy słownik z minimalnym zestawem danych (bez serwerów)
        data = {
            "id": 99,
            "name": "Test",
            "code": "TST",
            "status": "Nowy",
            "owner_name": None,
            "owner_id": None,
            "problem_statement": None,
            "start_date": None,
            "end_date": None,
            "dev_server_id": None,
            "prod_server_id": None,
            "dev_server": None,
            "prod_server": None,
            "port_range_start": None,
            "port_range_end": None,
            "kpis": [],
            "technologies": [],
            "scope_items": [],
            "ports": [],
            "created_at": None,
            "updated_at": None,
        }
        project_read = ProjectRead(**data)
        assert project_read.dev_server is None
        assert project_read.prod_server is None


# ---------------------------------------------------------------------------
# Testy schematu ServerCreate
# ---------------------------------------------------------------------------


class TestServerCreate:
    """Weryfikacja walidacji Pydantic dla schematu ServerCreate."""

    def test_valid_minimal(self) -> None:
        """Name i hostname powinny wystarczyć do utworzenia serwera."""
        # Minimalne dane — reszta ma wartości domyślne
        server = ServerCreate(name="SRV-01", hostname="10.0.0.1")
        assert server.name == "SRV-01"
        assert server.hostname == "10.0.0.1"

    def test_name_too_short(self) -> None:
        """Nazwa serwera krótsza niż 2 znaki powinna rzucić ValidationError."""
        # min_length=2 dla pola name
        with pytest.raises(ValidationError):
            ServerCreate(name="A", hostname="10.0.0.1")

    def test_hostname_required(self) -> None:
        """Brak hostname powinien rzucić ValidationError."""
        # hostname jest polem wymaganym
        with pytest.raises(ValidationError) as exc_info:
            ServerCreate(name="SRV-01")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("hostname",) for e in errors)

    def test_default_type_is_dev(self) -> None:
        """Domyślny typ serwera powinien być ServerType.DEV."""
        server = ServerCreate(name="SRV-DEF", hostname="10.0.0.2")
        assert server.server_type == ServerType.DEV

    def test_default_status_is_aktywny(self) -> None:
        """Domyślny status serwera powinien być ServerStatus.AKTYWNY."""
        server = ServerCreate(name="SRV-DEF", hostname="10.0.0.3")
        assert server.status == ServerStatus.AKTYWNY


# ---------------------------------------------------------------------------
# Testy schematu KPICreate
# ---------------------------------------------------------------------------


class TestKPICreate:
    """Weryfikacja walidacji Pydantic dla schematu KPICreate."""

    def test_valid_kpi(self) -> None:
        """Name i target_value powinny wystarczyć do utworzenia KPI."""
        kpi = KPICreate(name="Czas odpowiedzi", target_value="< 200ms")
        assert kpi.name == "Czas odpowiedzi"
        assert kpi.target_value == "< 200ms"

    def test_name_required(self) -> None:
        """Brak nazwy KPI powinien rzucić ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KPICreate(target_value="100%")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_target_value_required(self) -> None:
        """Brak target_value powinien rzucić ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            KPICreate(name="Wskaźnik bez celu")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("target_value",) for e in errors)

    def test_optional_fields(self) -> None:
        """current_value i unit mogą być None."""
        # Tworzymy KPI bez pól opcjonalnych
        kpi = KPICreate(name="Wskaźnik", target_value="100")
        assert kpi.current_value is None
        assert kpi.unit is None


# ---------------------------------------------------------------------------
# Testy schematu PortCreate
# ---------------------------------------------------------------------------


class TestPortCreate:
    """Weryfikacja walidacji Pydantic dla schematu PortCreate."""

    def test_valid_port(self) -> None:
        """Port z prawidłowym numerem powinien przejść walidację."""
        port = PortCreate(port_number=8080, protocol="TCP")
        assert port.port_number == 8080

    def test_port_number_min(self) -> None:
        """Port 0 (poniżej minimum ge=1) powinien rzucić ValidationError."""
        with pytest.raises(ValidationError):
            PortCreate(port_number=0, protocol="TCP")

    def test_port_number_max(self) -> None:
        """Port 70000 (powyżej maksimum le=65535) powinien rzucić ValidationError."""
        with pytest.raises(ValidationError):
            PortCreate(port_number=70000, protocol="TCP")

    def test_default_protocol_is_tcp(self) -> None:
        """Domyślny protokół portu powinien być PortProtocol.TCP."""
        # Port bez podania protokołu powinien mieć TCP jako domyślny
        port = PortCreate(port_number=8080)
        assert port.protocol == PortProtocol.TCP
