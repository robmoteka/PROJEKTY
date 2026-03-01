"""
Testy integracyjne endpointów FastAPI (module-issues/main.py).

Cel: weryfikacja że endpointy zwracają poprawne HTML partiale z atrybutami HTMX
oraz że interakcja z bazą danych działa poprawnie end-to-end.

Baza danych: SQLite in-memory (fixture z conftest.py)

Uruchomienie:
    cd module-issues && pytest tests/test_endpoints_integration.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET / — strona główna modułu
# ---------------------------------------------------------------------------

class TestIssuesHome:
    """Testy endpointu GET / — lista zgłoszeń."""

    def test_zwraca_200(self, client: TestClient) -> None:
        """GET / powinno zwrócić status 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_zwraca_html(self, client: TestClient) -> None:
        """GET / powinno zwrócić content-type text/html."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_zawiera_tabele(self, client: TestClient) -> None:
        """GET / powinno zawierać element <table w HTML."""
        response = client.get("/")
        assert "<table" in response.text

    def test_zawiera_przycisk_nowe_zgloszenie(self, client: TestClient) -> None:
        """GET / powinno zawierać przycisk do tworzenia nowego zgłoszenia z atrybutem hx-get."""
        response = client.get("/")
        assert "hx-get" in response.text
        assert "Nowe zgłoszenie" in response.text


# ---------------------------------------------------------------------------
# GET /list — lista zgłoszeń (HTMX swap)
# ---------------------------------------------------------------------------

class TestIssuesList:
    """Testy endpointu GET /list."""

    def test_zwraca_200_z_pustą_listą(self, client: TestClient) -> None:
        """GET /list na pustej bazie powinno zwrócić 200."""
        response = client.get("/list")
        assert response.status_code == 200

    def test_zwraca_wiersze_z_issues(self, client: TestClient, sample_issue) -> None:
        """GET /list powinno zawierać tytuł istniejącego zgłoszenia."""
        response = client.get("/list")
        assert response.status_code == 200
        assert sample_issue.title in response.text

    def test_wiersz_zawiera_atrybuty_htmx(self, client: TestClient, sample_issue) -> None:
        """Wiersze tabeli powinny zawierać atrybuty hx-delete i hx-get (HTMX)."""
        response = client.get("/list")
        assert "hx-delete" in response.text
        assert "hx-get" in response.text


# ---------------------------------------------------------------------------
# GET /create — formularz tworzenia
# ---------------------------------------------------------------------------

class TestCreateForm:
    """Testy endpointu GET /create."""

    def test_zwraca_200(self, client: TestClient) -> None:
        """GET /create powinno zwrócić formularz z kodem 200."""
        response = client.get("/create")
        assert response.status_code == 200

    def test_formularz_zawiera_hx_post(self, client: TestClient) -> None:
        """Formularz tworzenia powinien zawierać atrybut hx-post."""
        response = client.get("/create")
        assert "hx-post" in response.text

    def test_formularz_zawiera_pole_title(self, client: TestClient) -> None:
        """Formularz powinien zawierać pole input name=title."""
        response = client.get("/create")
        assert 'name="title"' in response.text


# ---------------------------------------------------------------------------
# POST /create — tworzenie zgłoszenia
# ---------------------------------------------------------------------------

class TestCreateIssueEndpoint:
    """Testy endpointu POST /create."""

    def test_tworzy_issue_i_zwraca_200(self, client: TestClient) -> None:
        """POST /create z poprawnymi danymi powinno zwrócić 200 i HTML."""
        response = client.post(
            "/create",
            data={"title": "Nowe zgłoszenie testowe", "priority": "Średni"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_nowe_issue_pojawia_sie_na_liscie(self, client: TestClient) -> None:
        """Po POST /create tytuł nowego zgłoszenia powinien być widoczny na liście."""
        client.post("/create", data={"title": "Zgłoszenie widoczne na liście", "priority": "Niski"})
        response = client.get("/list")
        assert "Zgłoszenie widoczne na liście" in response.text

    def test_przekazuje_dane_uzytkownika_z_naglowkow(self, client: TestClient) -> None:
        """POST /create z nagłówkami X-User-* powinno zapisać autora zgłoszenia."""
        response = client.post(
            "/create",
            data={"title": "Zgłoszenie z autorem", "priority": "Wysoki"},
            headers={"X-User-Sub": "user-sub-abc", "X-User-Name": "Tomasz Kowalczyk"},
        )
        assert response.status_code == 200
        # Sprawdzamy czy autor pojawia się na liście
        assert "Tomasz Kowalczyk" in response.text


# ---------------------------------------------------------------------------
# GET /{issue_id} — szczegóły zgłoszenia
# ---------------------------------------------------------------------------

class TestIssueDetail:
    """Testy endpointu GET /{issue_id}."""

    def test_zwraca_200_dla_istniejacego_id(self, client: TestClient, sample_issue) -> None:
        """GET /{id} dla istniejącego zgłoszenia powinno zwrócić 200."""
        response = client.get(f"/{sample_issue.id}")
        assert response.status_code == 200

    def test_zawiera_tytul_zgloszenia(self, client: TestClient, sample_issue) -> None:
        """GET /{id} powinno zawierać tytuł zgłoszenia w odpowiedzi HTML."""
        response = client.get(f"/{sample_issue.id}")
        assert sample_issue.title in response.text

    def test_zawiera_przycisk_edytuj(self, client: TestClient, sample_issue) -> None:
        """GET /{id} powinno zawierać przycisk edycji z hx-get."""
        response = client.get(f"/{sample_issue.id}")
        assert "hx-get" in response.text
        assert "Edytuj" in response.text

    def test_zwraca_404_dla_nieistniejacego_id(self, client: TestClient) -> None:
        """GET /{id} dla nieistniejącego ID powinno zwrócić status 404."""
        response = client.get("/99999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /{issue_id}/edit — formularz edycji
# ---------------------------------------------------------------------------

class TestEditForm:
    """Testy endpointu GET /{issue_id}/edit."""

    def test_zwraca_200_dla_istniejacego_id(self, client: TestClient, sample_issue) -> None:
        """GET /{id}/edit powinno zwrócić formularz edycji z kodem 200."""
        response = client.get(f"/{sample_issue.id}/edit")
        assert response.status_code == 200

    def test_formularz_zawiera_hx_put(self, client: TestClient, sample_issue) -> None:
        """Formularz edycji powinien zawierać atrybut hx-put."""
        response = client.get(f"/{sample_issue.id}/edit")
        assert "hx-put" in response.text

    def test_formularz_zawiera_istniejacy_tytul(self, client: TestClient, sample_issue) -> None:
        """Formularz edycji powinien być wstępnie wypełniony tytułem zgłoszenia."""
        response = client.get(f"/{sample_issue.id}/edit")
        assert sample_issue.title in response.text

    def test_zwraca_404_dla_nieistniejacego_id(self, client: TestClient) -> None:
        """GET /{id}/edit dla nieistniejącego ID powinno zwrócić 404."""
        response = client.get("/99999/edit")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /{issue_id} — aktualizacja zgłoszenia
# ---------------------------------------------------------------------------

class TestUpdateIssueEndpoint:
    """Testy endpointu PUT /{issue_id}."""

    def test_aktualizuje_tytul(self, client: TestClient, sample_issue) -> None:
        """PUT /{id} z nowym tytułem powinno zaktualizować zgłoszenie."""
        response = client.put(
            f"/{sample_issue.id}",
            data={"title": "Zaktualizowany tytuł zgłoszenia", "status": "W toku"},
        )
        assert response.status_code == 200
        assert "Zaktualizowany tytuł zgłoszenia" in response.text

    def test_zwraca_html_z_atrybutami_htmx(self, client: TestClient, sample_issue) -> None:
        """PUT /{id} powinno zwrócić HTML partial z atrybutami HTMX."""
        response = client.put(
            f"/{sample_issue.id}",
            data={"title": "Tytuł po update", "status": "Nowy"},
        )
        assert "hx-delete" in response.text or "hx-get" in response.text


# ---------------------------------------------------------------------------
# DELETE /{issue_id} — usunięcie zgłoszenia
# ---------------------------------------------------------------------------

class TestDeleteIssueEndpoint:
    """Testy endpointu DELETE /{issue_id}."""

    def test_zwraca_200_po_usunieciu(self, client: TestClient, sample_issue) -> None:
        """DELETE /{id} dla istniejącego zgłoszenia powinno zwrócić 200."""
        response = client.delete(f"/{sample_issue.id}")
        assert response.status_code == 200

    def test_zwraca_pusty_response_po_usunieciu(self, client: TestClient, sample_issue) -> None:
        """DELETE /{id} powinno zwrócić pusty body (HTMX outerHTML swap usuwa element)."""
        response = client.delete(f"/{sample_issue.id}")
        assert response.content == b""

    def test_issue_nie_istnieje_po_usunieciu(self, client: TestClient, sample_issue) -> None:
        """Po DELETE /{id}, GET /{id} powinno zwrócić 404."""
        client.delete(f"/{sample_issue.id}")
        response = client.get(f"/{sample_issue.id}")
        assert response.status_code == 404

    def test_usuniecie_nieistniejacego_id_zwraca_200(self, client: TestClient) -> None:
        """DELETE /{id} dla nieistniejącego ID powinno zwrócić 200 (idempotentność)."""
        response = client.delete("/99999")
        assert response.status_code == 200
