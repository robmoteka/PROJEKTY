"""
Testy jednostkowe modeli SQLAlchemy (module-issues/models.py).

Cel: weryfikacja wartości enumów, domyślnych kolumn i struktury modelu Issue.
Baza danych: SQLite in-memory (fixture z conftest.py).

Uruchomienie:
    cd module-issues && pytest tests/test_models_unit.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from models import Issue, IssuePriority, IssueStatus


# ---------------------------------------------------------------------------
# Testy enumu IssueStatus
# ---------------------------------------------------------------------------

class TestIssueStatusEnum:
    """Weryfikacja że enum IssueStatus ma poprawne wartości string."""

    def test_status_nowy_ma_poprawna_wartosc(self) -> None:
        """IssueStatus.NOWY powinno mieć wartość 'Nowy'."""
        assert IssueStatus.NOWY.value == "Nowy"

    def test_status_w_toku_ma_poprawna_wartosc(self) -> None:
        """IssueStatus.W_TOKU powinno mieć wartość 'W toku'."""
        assert IssueStatus.W_TOKU.value == "W toku"

    def test_status_do_weryfikacji_ma_poprawna_wartosc(self) -> None:
        """IssueStatus.DO_WERYFIKACJI powinno mieć wartość 'Do weryfikacji'."""
        assert IssueStatus.DO_WERYFIKACJI.value == "Do weryfikacji"

    def test_status_zamkniety_ma_poprawna_wartosc(self) -> None:
        """IssueStatus.ZAMKNIETY powinno mieć wartość 'Zamknięty'."""
        assert IssueStatus.ZAMKNIETY.value == "Zamknięty"

    def test_enum_jest_podtypem_str(self) -> None:
        """IssueStatus powinno dziedziczyć po str — umożliwia bezpośrednie porównanie."""
        assert isinstance(IssueStatus.NOWY, str)
        assert IssueStatus.NOWY == "Nowy"

    def test_wszystkie_statusy_sa_dostepne(self) -> None:
        """IssueStatus powinno mieć dokładnie 4 wartości."""
        assert len(list(IssueStatus)) == 4


# ---------------------------------------------------------------------------
# Testy enumu IssuePriority
# ---------------------------------------------------------------------------

class TestIssuePriorityEnum:
    """Weryfikacja że enum IssuePriority ma poprawne wartości string."""

    def test_priorytet_niski_ma_poprawna_wartosc(self) -> None:
        """IssuePriority.NISKI powinno mieć wartość 'Niski'."""
        assert IssuePriority.NISKI.value == "Niski"

    def test_priorytet_sredni_ma_poprawna_wartosc(self) -> None:
        """IssuePriority.SREDNI powinno mieć wartość 'Średni'."""
        assert IssuePriority.SREDNI.value == "Średni"

    def test_priorytet_wysoki_ma_poprawna_wartosc(self) -> None:
        """IssuePriority.WYSOKI powinno mieć wartość 'Wysoki'."""
        assert IssuePriority.WYSOKI.value == "Wysoki"

    def test_priorytet_krytyczny_ma_poprawna_wartosc(self) -> None:
        """IssuePriority.KRYTYCZNY powinno mieć wartość 'Krytyczny'."""
        assert IssuePriority.KRYTYCZNY.value == "Krytyczny"

    def test_enum_jest_podtypem_str(self) -> None:
        """IssuePriority powinno dziedziczyć po str — umożliwia bezpośrednie porównanie."""
        assert isinstance(IssuePriority.KRYTYCZNY, str)
        assert IssuePriority.KRYTYCZNY == "Krytyczny"

    def test_wszystkie_priorytety_sa_dostepne(self) -> None:
        """IssuePriority powinno mieć dokładnie 4 wartości."""
        assert len(list(IssuePriority)) == 4


# ---------------------------------------------------------------------------
# Testy modelu Issue — domyślne wartości kolumn
# ---------------------------------------------------------------------------

class TestIssueModel:
    """Weryfikacja domyślnych wartości i struktury modelu Issue."""

    def test_issue_ma_domyslny_status_nowy(self, db_session: Session) -> None:
        """Nowy Issue bez podanego statusu powinien mieć status 'Nowy'."""
        # Tworzymy issue bez jawnego ustawiania statusu
        issue = Issue(
            title="Testowe zgłoszenie",
            author_id="sub-001",
            author_name="Testowy Użytkownik",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        # Domyślna wartość statusu pochodzi z definicji kolumny
        assert issue.status == IssueStatus.NOWY.value

    def test_issue_ma_domyslny_priorytet_sredni(self, db_session: Session) -> None:
        """Nowy Issue bez podanego priorytetu powinien mieć priorytet 'Średni'."""
        issue = Issue(
            title="Zgłoszenie z domyślnym priorytetem",
            author_id="sub-002",
            author_name="Testowy Użytkownik",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        # Domyślna wartość priorytetu pochodzi z definicji kolumny
        assert issue.priority == IssuePriority.SREDNI.value

    def test_issue_ma_id_po_zapisie(self, db_session: Session) -> None:
        """Issue powinno dostać id (klucz główny) po zapisaniu do bazy."""
        issue = Issue(title="Zgłoszenie z ID", author_id="sub-003", author_name="Autor")
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        # Klucz główny przypisany przez bazę
        assert issue.id is not None
        assert isinstance(issue.id, int)
        assert issue.id > 0

    def test_issue_pola_opcjonalne_sa_none(self, db_session: Session) -> None:
        """Opcjonalne pola (description, assignee_*) powinny mieć wartość None jeśli nie podane."""
        issue = Issue(title="Minimalne zgłoszenie", author_id="sub-004", author_name="Autor")
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        # Pola opcjonalne — nullable=True w modelu
        assert issue.description is None
        assert issue.assignee_id is None
        assert issue.assignee_name is None

    def test_issue_przechowuje_podany_tytul(self, db_session: Session) -> None:
        """Issue powinno zachować dokładnie podany tytuł."""
        tytul = "Tytuł z polskimi znakami: ąęśćółźż"
        issue = Issue(title=tytul, author_id="sub-005", author_name="Autor")
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        assert issue.title == tytul

    def test_dwa_issues_maja_rozne_id(self, db_session: Session) -> None:
        """Dwa issues powinny mieć różne klucze główne (auto-increment)."""
        issue1 = Issue(title="Pierwsze zgłoszenie", author_id="sub-006", author_name="Autor")
        issue2 = Issue(title="Drugie zgłoszenie", author_id="sub-006", author_name="Autor")
        db_session.add_all([issue1, issue2])
        db_session.commit()
        db_session.refresh(issue1)
        db_session.refresh(issue2)

        # Każdy rekord ma unikalny klucz główny
        assert issue1.id != issue2.id

    def test_issue_przechowuje_priorytet_krytyczny(self, db_session: Session) -> None:
        """Issue z jawnie podanym priorytetem Krytyczny powinno go zachować."""
        issue = Issue(
            title="Krytyczny błąd produkcyjny",
            priority=IssuePriority.KRYTYCZNY.value,
            author_id="sub-007",
            author_name="Autor",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        assert issue.priority == IssuePriority.KRYTYCZNY.value

    def test_issue_przechowuje_status_w_toku(self, db_session: Session) -> None:
        """Issue z jawnie ustawionym statusem W toku powinno go zachować."""
        issue = Issue(
            title="Zadanie w realizacji",
            status=IssueStatus.W_TOKU.value,
            author_id="sub-008",
            author_name="Autor",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        assert issue.status == IssueStatus.W_TOKU.value
