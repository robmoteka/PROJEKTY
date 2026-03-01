"""
Testy jednostkowe operacji CRUD (module-issues/crud.py).

Cel: weryfikacja logiki biznesowej w izolacji od reszty aplikacji.
Baza danych: SQLite in-memory (bez PostgreSQL).

Uruchomienie:
    cd module-issues && pytest tests/test_crud_unit.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from crud import (
    create_issue,
    delete_issue,
    get_issue_by_id,
    get_issues,
    update_issue,
)
from models import IssueStatus, IssuePriority
from schemas import IssueCreate, IssueUpdate


# ---------------------------------------------------------------------------
# Testy create_issue
# ---------------------------------------------------------------------------

class TestCreateIssue:
    """Testy funkcji create_issue — tworzenie nowego zgłoszenia."""

    def test_tworzy_issue_z_poprawnymi_polami(self, db_session: Session) -> None:
        """create_issue powinno zapisać rekord z tytułem, autorem i domyślnym statusem."""
        issue_data = IssueCreate(title="Problem z logowaniem", description="Użytkownik nie może się zalogować")
        issue = create_issue(db_session, issue_data, author_id="sub-001", author_name="Anna Kowalska")

        # Sprawdzamy pola podstawowe
        assert issue.id is not None
        assert issue.title == "Problem z logowaniem"
        assert issue.description == "Użytkownik nie może się zalogować"
        assert issue.author_id == "sub-001"
        assert issue.author_name == "Anna Kowalska"
        # Status domyślny to "Nowy"
        assert issue.status == IssueStatus.NOWY.value

    def test_tworzy_issue_z_priorytetem_wysoki(self, db_session: Session) -> None:
        """create_issue z priorytetem Wysoki powinno zapisać właściwą wartość."""
        issue_data = IssueCreate(title="Krytyczny błąd", priority=IssuePriority.WYSOKI)
        issue = create_issue(db_session, issue_data, author_id="sub-002", author_name="Piotr Nowak")

        assert issue.priority == IssuePriority.WYSOKI.value

    def test_tworzy_issue_z_assignee(self, db_session: Session) -> None:
        """create_issue z podanym assignee powinno zapisać dane przypisanej osoby."""
        issue_data = IssueCreate(
            title="Zadanie dla Jana",
            assignee_id="sub-jan-999",
            assignee_name="Jan Kowalski",
        )
        issue = create_issue(db_session, issue_data, author_id="sub-003", author_name="Manager")

        assert issue.assignee_id == "sub-jan-999"
        assert issue.assignee_name == "Jan Kowalski"

    def test_opis_moze_byc_none(self, db_session: Session) -> None:
        """create_issue bez opisu powinno zapisać None w polu description."""
        issue_data = IssueCreate(title="Issue bez opisu")
        issue = create_issue(db_session, issue_data, author_id="sub-004", author_name="Autor")

        assert issue.description is None


# ---------------------------------------------------------------------------
# Testy get_issues
# ---------------------------------------------------------------------------

class TestGetIssues:
    """Testy funkcji get_issues — pobieranie listy zgłoszeń."""

    def test_zwraca_pusta_liste_gdy_brak_issues(self, db_session: Session) -> None:
        """get_issues na pustej bazie powinno zwrócić pustą listę, nie None."""
        result = get_issues(db_session)
        assert result == []

    def test_zwraca_liste_z_kilkoma_issues(self, db_session: Session) -> None:
        """get_issues powinno zwrócić wszystkie istniejące zgłoszenia."""
        # Tworzymy 3 zgłoszenia
        for i in range(1, 4):
            issue_data = IssueCreate(title=f"Issue {i}")
            create_issue(db_session, issue_data, author_id=f"sub-{i}", author_name=f"Autor {i}")

        result = get_issues(db_session)
        assert len(result) == 3

    def test_filtruje_po_statusie(self, db_session: Session) -> None:
        """get_issues z filtrem statusu powinno zwrócić tylko pasujące rekordy."""
        # Tworzymy issue i zmieniamy jego status
        issue_data = IssueCreate(title="Issue W toku")
        created = create_issue(db_session, issue_data, author_id="sub-x", author_name="X")
        # Ręczna aktualizacja statusu
        created.status = IssueStatus.W_TOKU.value
        db_session.commit()
        db_session.refresh(created)

        # Tworzymy drugie issue z domyślnym statusem "Nowy"
        issue_data2 = IssueCreate(title="Issue Nowy")
        create_issue(db_session, issue_data2, author_id="sub-y", author_name="Y")

        # Filtrujemy po statusie "W toku"
        result = get_issues(db_session, status=IssueStatus.W_TOKU.value)
        assert len(result) == 1
        assert result[0].status == IssueStatus.W_TOKU.value

    def test_paginacja_skip_i_limit(self, db_session: Session) -> None:
        """get_issues powinno obsługiwać skip i limit poprawnie."""
        # Tworzymy 5 zgłoszeń
        for i in range(1, 6):
            issue_data = IssueCreate(title=f"Issue paginacja {i}")
            create_issue(db_session, issue_data, author_id=f"sub-{i}", author_name=f"Autor {i}")

        # Pobieramy z offsetem 2 i limitem 2
        result = get_issues(db_session, skip=2, limit=2)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Testy get_issue_by_id
# ---------------------------------------------------------------------------

class TestGetIssueById:
    """Testy funkcji get_issue_by_id — pobieranie pojedynczego zgłoszenia."""

    def test_zwraca_issue_dla_istniejacego_id(self, db_session: Session, sample_issue) -> None:
        """get_issue_by_id powinno zwrócić issue dla prawidłowego ID."""
        result = get_issue_by_id(db_session, sample_issue.id)
        assert result is not None
        assert result.id == sample_issue.id
        assert result.title == sample_issue.title

    def test_zwraca_none_dla_nieistniejacego_id(self, db_session: Session) -> None:
        """get_issue_by_id powinno zwrócić None jeśli ID nie istnieje."""
        result = get_issue_by_id(db_session, 99999)
        assert result is None


# ---------------------------------------------------------------------------
# Testy update_issue
# ---------------------------------------------------------------------------

class TestUpdateIssue:
    """Testy funkcji update_issue — aktualizacja zgłoszenia (partial update)."""

    def test_aktualizuje_tylko_podane_pola(self, db_session: Session, sample_issue) -> None:
        """update_issue powinno zmienić tylko pola zawarte w IssueUpdate."""
        original_description = sample_issue.description
        update_data = IssueUpdate(title="Zmieniony tytuł")
        updated = update_issue(db_session, sample_issue.id, update_data)

        assert updated is not None
        assert updated.title == "Zmieniony tytuł"
        # Opis powinien pozostać bez zmian
        assert updated.description == original_description

    def test_aktualizuje_status(self, db_session: Session, sample_issue) -> None:
        """update_issue powinno poprawnie zmienić status zgłoszenia."""
        update_data = IssueUpdate(status=IssueStatus.ZAMKNIETY)
        updated = update_issue(db_session, sample_issue.id, update_data)

        assert updated is not None
        assert updated.status == IssueStatus.ZAMKNIETY.value

    def test_zwraca_none_dla_nieistniejacego_id(self, db_session: Session) -> None:
        """update_issue powinno zwrócić None jeśli issue nie istnieje."""
        update_data = IssueUpdate(title="Nowy tytuł")
        result = update_issue(db_session, 99999, update_data)
        assert result is None


# ---------------------------------------------------------------------------
# Testy delete_issue
# ---------------------------------------------------------------------------

class TestDeleteIssue:
    """Testy funkcji delete_issue — usuwanie zgłoszenia."""

    def test_zwraca_true_po_usunieciu(self, db_session: Session, sample_issue) -> None:
        """delete_issue powinno zwrócić True jeśli issue istniało i zostało usunięte."""
        result = delete_issue(db_session, sample_issue.id)
        assert result is True

    def test_issue_nie_istnieje_po_usunieciu(self, db_session: Session, sample_issue) -> None:
        """Po usunięciu get_issue_by_id powinno zwrócić None."""
        delete_issue(db_session, sample_issue.id)
        result = get_issue_by_id(db_session, sample_issue.id)
        assert result is None

    def test_zwraca_false_dla_nieistniejacego_id(self, db_session: Session) -> None:
        """delete_issue powinno zwrócić False jeśli issue nie istnieje."""
        result = delete_issue(db_session, 99999)
        assert result is False
