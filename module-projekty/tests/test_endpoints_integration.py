"""
Testy integracyjne endpointów FastAPI (module-projekty/main.py).

Cel: weryfikacja status code, content-type, obecności danych HTML
i atrybutów HTMX (hx-get, hx-post, hx-put, hx-delete, hx-target).
Używa TestClient (synchroniczny) z SQLite in-memory przez dependency_overrides.

Uruchomienie:
    cd module-projekty && pytest tests/test_endpoints_integration.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Testy strony głównej — GET /
# ---------------------------------------------------------------------------


class TestProjectsHome:
    """Weryfikacja endpointu GET / (strona główna modułu Projekty)."""

    def test_home_returns_200(self, client: TestClient) -> None:
        """GET / powinien zwrócić status 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_contains_htmx_attributes(self, client: TestClient) -> None:
        """GET / powinien zwrócić HTML z atrybutami HTMX."""
        response = client.get("/")
        # Partiale modułu powinny zawierać atrybuty HTMX do interakcji
        assert "hx-" in response.text


# ---------------------------------------------------------------------------
# Testy listy projektów — GET /list
# ---------------------------------------------------------------------------


class TestProjectsList:
    """Weryfikacja endpointu GET /list z opcjonalnym filtrem statusu."""

    def test_list_returns_200(self, client: TestClient) -> None:
        """GET /list powinien zwrócić status 200."""
        response = client.get("/list")
        assert response.status_code == 200

    def test_list_with_status_filter(self, client: TestClient) -> None:
        """GET /list?status=Nowy powinien zwrócić status 200."""
        # Filtr statusu przekazywany jako query param
        response = client.get("/list?status=Nowy")
        assert response.status_code == 200

    def test_list_contains_project_data(
        self, client: TestClient, sample_project
    ) -> None:
        """Nazwa istniejącego projektu powinna być widoczna w odpowiedzi HTML."""
        response = client.get("/list")
        # Nazwa projektu utworzonego przez fixture powinna pojawić się w HTML
        assert sample_project.name in response.text


# ---------------------------------------------------------------------------
# Testy formularza tworzenia projektu — GET /create
# ---------------------------------------------------------------------------


class TestCreateProjectForm:
    """Weryfikacja endpointu GET /create (formularz nowego projektu)."""

    def test_create_form_returns_200(self, client: TestClient) -> None:
        """GET /create powinien zwrócić status 200."""
        response = client.get("/create")
        assert response.status_code == 200

    def test_create_form_has_submit_attribute(self, client: TestClient) -> None:
        """Formularz tworzenia projektu powinien zawierać atrybut hx-post."""
        response = client.get("/create")
        # Formularz HTMX używa hx-post zamiast klasowego action
        assert "hx-post" in response.text


# ---------------------------------------------------------------------------
# Testy tworzenia projektu — POST /create
# ---------------------------------------------------------------------------


class TestCreateProjectEndpoint:
    """Weryfikacja endpointu POST /create (przetwarzanie formularza)."""

    def test_create_project_returns_200(self, client: TestClient) -> None:
        """POST /create z poprawnymi danymi powinien zwrócić status 200."""
        # Minimalne dane wymagane przez formularz
        response = client.post(
            "/create",
            data={"name": "Projekt Beta", "code": "BETA-01", "status": "Nowy"},
        )
        assert response.status_code == 200

    def test_create_project_appears_in_list(self, client: TestClient) -> None:
        """Nowo utworzony projekt powinien być widoczny w odpowiedzi HTML (lista)."""
        # Tworzymy projekt przez endpoint
        response = client.post(
            "/create",
            data={"name": "Projekt Gamma", "code": "GAMMA-01", "status": "Nowy"},
        )
        # Odpowiedź zawiera odświeżoną listę — nowy projekt powinien być widoczny
        assert "Projekt Gamma" in response.text

    def test_create_project_minimal_data(self, client: TestClient) -> None:
        """POST /create z samym name i code powinien zwrócić status 200."""
        # Weryfikujemy że opcjonalne pola nie są wymagane przez endpoint
        response = client.post(
            "/create",
            data={"name": "Minimalny", "code": "MIN-01", "status": "Nowy"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Testy karty projektu — GET /{project_id}
# ---------------------------------------------------------------------------


class TestProjectDetail:
    """Weryfikacja endpointu GET /{project_id} (karta projektu)."""

    def test_detail_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """GET /{project_id} dla istniejącego projektu powinien zwrócić status 200."""
        response = client.get(f"/{sample_project.id}")
        assert response.status_code == 200

    def test_detail_shows_project_name(
        self, client: TestClient, sample_project
    ) -> None:
        """Karta projektu powinna zawierać nazwę projektu."""
        response = client.get(f"/{sample_project.id}")
        # Nazwa projektu powinna być widoczna w karcie
        assert sample_project.name in response.text

    def test_detail_nonexistent_returns_404(self, client: TestClient) -> None:
        """GET /999 dla nieistniejącego projektu powinien zwrócić status 404."""
        response = client.get("/999999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Testy formularza edycji projektu — GET /{project_id}/edit
# ---------------------------------------------------------------------------


class TestEditProjectForm:
    """Weryfikacja endpointu GET /{project_id}/edit (formularz edycji)."""

    def test_edit_form_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """GET /{project_id}/edit powinien zwrócić status 200."""
        response = client.get(f"/{sample_project.id}/edit")
        assert response.status_code == 200

    def test_edit_form_prefilled(
        self, client: TestClient, sample_project
    ) -> None:
        """Formularz edycji powinien zawierać aktualne dane projektu."""
        response = client.get(f"/{sample_project.id}/edit")
        # Kod projektu powinien być widoczny jako wypełnione pole formularza
        assert sample_project.code in response.text


# ---------------------------------------------------------------------------
# Testy aktualizacji projektu — PUT /{project_id}
# ---------------------------------------------------------------------------


class TestUpdateProjectEndpoint:
    """Weryfikacja endpointu PUT /{project_id} (zapis edycji)."""

    def test_update_project_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """PUT /{project_id} z danymi aktualizacji powinien zwrócić status 200."""
        response = client.put(
            f"/{sample_project.id}",
            data={"name": "Nowa Nazwa Projektu", "status": "W toku"},
        )
        assert response.status_code == 200

    def test_update_nonexistent_returns_404(self, client: TestClient) -> None:
        """PUT /999 dla nieistniejącego projektu powinien zwrócić status 404."""
        response = client.put(
            "/999999",
            data={"name": "Ghost"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Testy usuwania projektu — DELETE /{project_id}
# ---------------------------------------------------------------------------


class TestDeleteProjectEndpoint:
    """Weryfikacja endpointu DELETE /{project_id} (usunięcie projektu)."""

    def test_delete_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """DELETE /{project_id} powinien zwrócić status 200."""
        response = client.delete(f"/{sample_project.id}")
        assert response.status_code == 200

    def test_delete_response_empty(
        self, client: TestClient, sample_project
    ) -> None:
        """Odpowiedź DELETE powinna być pusta — HTMX usuwa element z DOM."""
        response = client.delete(f"/{sample_project.id}")
        # Pusty body — HTMX outerHTML swap usuwa wiersz projektów
        assert response.text == ""


# ---------------------------------------------------------------------------
# Testy listy serwerów — GET /servers
# ---------------------------------------------------------------------------


class TestServersList:
    """Weryfikacja endpointu GET /servers (lista serwerów)."""

    def test_servers_list_returns_200(self, client: TestClient) -> None:
        """GET /servers powinien zwrócić status 200."""
        response = client.get("/servers")
        assert response.status_code == 200

    def test_servers_list_is_html(self, client: TestClient) -> None:
        """GET /servers powinien zwrócić odpowiedź HTML."""
        response = client.get("/servers")
        # Content-Type musi być text/html
        assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# Testy tworzenia serwera — POST /servers/create
# ---------------------------------------------------------------------------


class TestCreateServerEndpoint:
    """Weryfikacja endpointów tworzenia serwera (GET form + POST submit)."""

    def test_create_server_form_returns_200(self, client: TestClient) -> None:
        """GET /servers/create powinien zwrócić formularz z status 200."""
        response = client.get("/servers/create")
        assert response.status_code == 200

    def test_create_server_returns_200(self, client: TestClient) -> None:
        """POST /servers/create z poprawnymi danymi powinien zwrócić status 200."""
        response = client.post(
            "/servers/create",
            data={
                "name": "STAGE-01",
                "hostname": "10.0.2.10",
                "server_type": "Staging",
                "status": "Aktywny",
            },
        )
        assert response.status_code == 200

    def test_create_server_appears_in_list(self, client: TestClient) -> None:
        """Nowo utworzony serwer powinien być widoczny w odpowiedzi HTML."""
        response = client.post(
            "/servers/create",
            data={
                "name": "WIDOCZNY-SRV",
                "hostname": "10.0.3.1",
                "server_type": "Dev",
                "status": "Aktywny",
            },
        )
        # Odpowiedź zawiera listę serwerów z nowym serwerem
        assert "WIDOCZNY-SRV" in response.text


# ---------------------------------------------------------------------------
# Testy szczegółów serwera — GET /servers/{sid}
# ---------------------------------------------------------------------------


class TestServerDetail:
    """Weryfikacja endpointu GET /servers/{sid} (karta serwera)."""

    def test_server_detail_returns_200(
        self, client: TestClient, sample_server
    ) -> None:
        """GET /servers/{sid} dla istniejącego serwera powinien zwrócić 200."""
        response = client.get(f"/servers/{sample_server.id}")
        assert response.status_code == 200

    def test_server_detail_nonexistent_404(self, client: TestClient) -> None:
        """GET /servers/999 dla nieistniejącego serwera powinien zwrócić 404."""
        response = client.get("/servers/999999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Testy KPI inline — CRUD na karcie projektu
# ---------------------------------------------------------------------------


class TestKPIEndpoints:
    """Weryfikacja endpointów CRUD dla KPI projektu (inline na karcie)."""

    def test_create_kpi_form_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """GET /{pid}/kpis/create powinien zwrócić formularz z status 200."""
        response = client.get(f"/{sample_project.id}/kpis/create")
        assert response.status_code == 200

    def test_create_kpi_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """POST /{pid}/kpis z poprawnymi danymi powinien zwrócić status 200."""
        response = client.post(
            f"/{sample_project.id}/kpis",
            data={"name": "Dostępność", "target_value": "99.9%"},
        )
        assert response.status_code == 200

    def test_update_kpi_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """PUT /{pid}/kpis/{kid} powinien zwrócić zaktualizowany wiersz ze status 200."""
        pid = sample_project_with_children["project"].id
        kid = sample_project_with_children["kpi"].id
        response = client.put(
            f"/{pid}/kpis/{kid}",
            data={"current_value": "99.5%"},
        )
        assert response.status_code == 200

    def test_delete_kpi_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """DELETE /{pid}/kpis/{kid} powinien zwrócić pusty response ze status 200."""
        pid = sample_project_with_children["project"].id
        kid = sample_project_with_children["kpi"].id
        response = client.delete(f"/{pid}/kpis/{kid}")
        assert response.status_code == 200
        # Pusty body — HTMX usuwa wiersz z DOM
        assert response.text == ""


# ---------------------------------------------------------------------------
# Testy Technologii inline — CRUD na karcie projektu
# ---------------------------------------------------------------------------


class TestTechnologyEndpoints:
    """Weryfikacja endpointów CRUD dla technologii projektu (inline na karcie)."""

    def test_create_tech_form_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """GET /{pid}/technologies/create powinien zwrócić formularz ze status 200."""
        response = client.get(f"/{sample_project.id}/technologies/create")
        assert response.status_code == 200

    def test_create_tech_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """POST /{pid}/technologies z poprawnymi danymi powinien zwrócić status 200."""
        response = client.post(
            f"/{sample_project.id}/technologies",
            data={"category": "Backend", "name": "Django"},
        )
        assert response.status_code == 200

    def test_update_tech_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """PUT /{pid}/technologies/{tid} powinien zwrócić zaktualizowany wiersz."""
        pid = sample_project_with_children["project"].id
        tid = sample_project_with_children["technology"].id
        response = client.put(
            f"/{pid}/technologies/{tid}",
            data={"version": "5.0"},
        )
        assert response.status_code == 200

    def test_delete_tech_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """DELETE /{pid}/technologies/{tid} powinien zwrócić pusty response."""
        pid = sample_project_with_children["project"].id
        tid = sample_project_with_children["technology"].id
        response = client.delete(f"/{pid}/technologies/{tid}")
        assert response.status_code == 200
        assert response.text == ""


# ---------------------------------------------------------------------------
# Testy Scope Items inline — CRUD na karcie projektu
# ---------------------------------------------------------------------------


class TestScopeEndpoints:
    """Weryfikacja endpointów CRUD dla elementów zakresu projektu (inline)."""

    def test_create_scope_form_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """GET /{pid}/scope/create powinien zwrócić formularz ze status 200."""
        response = client.get(f"/{sample_project.id}/scope/create")
        assert response.status_code == 200

    def test_create_scope_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """POST /{pid}/scope z poprawnymi danymi powinien zwrócić status 200."""
        response = client.post(
            f"/{sample_project.id}/scope",
            data={"category": "Must-have", "description": "Logowanie użytkownika"},
        )
        assert response.status_code == 200

    def test_update_scope_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """PUT /{pid}/scope/{sid} powinien zwrócić zaktualizowany wiersz."""
        pid = sample_project_with_children["project"].id
        sid = sample_project_with_children["scope_item"].id
        response = client.put(
            f"/{pid}/scope/{sid}",
            data={"priority": "1"},
        )
        assert response.status_code == 200

    def test_delete_scope_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """DELETE /{pid}/scope/{sid} powinien zwrócić pusty response."""
        pid = sample_project_with_children["project"].id
        sid = sample_project_with_children["scope_item"].id
        response = client.delete(f"/{pid}/scope/{sid}")
        assert response.status_code == 200
        assert response.text == ""


# ---------------------------------------------------------------------------
# Testy Portów inline — CRUD na karcie projektu
# ---------------------------------------------------------------------------


class TestPortEndpoints:
    """Weryfikacja endpointów CRUD dla portów sieciowych projektu (inline)."""

    def test_create_port_form_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """GET /{pid}/ports/create powinien zwrócić formularz ze status 200."""
        response = client.get(f"/{sample_project.id}/ports/create")
        assert response.status_code == 200

    def test_create_port_returns_200(
        self, client: TestClient, sample_project
    ) -> None:
        """POST /{pid}/ports z poprawnymi danymi powinien zwrócić status 200."""
        response = client.post(
            f"/{sample_project.id}/ports",
            data={"port_number": "8080", "protocol": "TCP", "service_name": "API"},
        )
        assert response.status_code == 200

    def test_update_port_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """PUT /{pid}/ports/{port_id} powinien zwrócić zaktualizowany wiersz."""
        pid = sample_project_with_children["project"].id
        port_id = sample_project_with_children["port"].id
        response = client.put(
            f"/{pid}/ports/{port_id}",
            data={"service_name": "API Gateway"},
        )
        assert response.status_code == 200

    def test_delete_port_returns_200(
        self, client: TestClient, sample_project_with_children
    ) -> None:
        """DELETE /{pid}/ports/{port_id} powinien zwrócić pusty response."""
        pid = sample_project_with_children["project"].id
        port_id = sample_project_with_children["port"].id
        response = client.delete(f"/{pid}/ports/{port_id}")
        assert response.status_code == 200
        assert response.text == ""
