"""
Testy jednostkowe schematów Pydantic (module-issues/schemas.py).

Cel: weryfikacja walidacji danych wejściowych i wyjściowych bez udziału bazy.

Uruchomienie:
    cd module-issues && pytest tests/test_schemas_unit.py -v
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models import IssuePriority, IssueStatus
from schemas import IssueCreate, IssueRead, IssueUpdate


# ---------------------------------------------------------------------------
# Testy IssueCreate
# ---------------------------------------------------------------------------

class TestIssueCreate:
    """Testy walidacji schematu tworzenia zgłoszenia."""

    def test_poprawne_dane_minimalne(self) -> None:
        """IssueCreate z samym tytułem (≥3 znaki) powinno przejść walidację."""
        issue = IssueCreate(title="Bug")
        assert issue.title == "Bug"
        # Wartości domyślne
        assert issue.description is None
        assert issue.priority == IssuePriority.SREDNI
        assert issue.assignee_id is None

    def test_poprawne_dane_pelne(self) -> None:
        """IssueCreate z wszystkimi polami powinno zmapować wszystkie wartości."""
        issue = IssueCreate(
            title="Pełne zgłoszenie",
            description="Szczegółowy opis",
            priority=IssuePriority.KRYTYCZNY,
            assignee_id="user-sub-123",
            assignee_name="Marek Testowy",
        )
        assert issue.title == "Pełne zgłoszenie"
        assert issue.description == "Szczegółowy opis"
        assert issue.priority == IssuePriority.KRYTYCZNY
        assert issue.assignee_id == "user-sub-123"
        assert issue.assignee_name == "Marek Testowy"

    def test_blad_gdy_pusty_tytul(self) -> None:
        """IssueCreate z pustym tytułem powinno rzucić ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            IssueCreate(title="")
        # Sprawdzamy że błąd dotyczy pola title
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_blad_gdy_tytul_za_krotki(self) -> None:
        """IssueCreate z tytułem < 3 znaki powinno rzucić ValidationError."""
        with pytest.raises(ValidationError):
            IssueCreate(title="AB")

    def test_blad_gdy_tytul_za_dlugi(self) -> None:
        """IssueCreate z tytułem > 255 znaków powinno rzucić ValidationError."""
        with pytest.raises(ValidationError):
            IssueCreate(title="A" * 256)

    def test_tytul_dokladnie_3_znaki(self) -> None:
        """IssueCreate z tytułem dokładnie 3 znaków (minimum) powinno przejść."""
        issue = IssueCreate(title="ABC")
        assert issue.title == "ABC"

    def test_tytul_dokladnie_255_znakow(self) -> None:
        """IssueCreate z tytułem dokładnie 255 znaków (maximum) powinno przejść."""
        issue = IssueCreate(title="A" * 255)
        assert len(issue.title) == 255

    def test_blad_gdy_brak_tytulu(self) -> None:
        """IssueCreate bez podania tytułu (required field) powinno rzucić ValidationError."""
        with pytest.raises(ValidationError):
            IssueCreate()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Testy IssueUpdate
# ---------------------------------------------------------------------------

class TestIssueUpdate:
    """Testy walidacji schematu aktualizacji zgłoszenia."""

    def test_wszystkie_pola_opcjonalne(self) -> None:
        """IssueUpdate bez żadnych pól powinno być poprawne (wszystko None)."""
        update = IssueUpdate()
        assert update.title is None
        assert update.description is None
        assert update.status is None
        assert update.priority is None
        assert update.assignee_id is None
        assert update.assignee_name is None

    def test_aktualizacja_tylko_tytulu(self) -> None:
        """IssueUpdate z samym tytułem powinno pomijać pozostałe pola."""
        update = IssueUpdate(title="Zaktualizowany tytuł")
        assert update.title == "Zaktualizowany tytuł"
        assert update.status is None

    def test_aktualizacja_statusu(self) -> None:
        """IssueUpdate z statusem powinno przyjąć wartość enum."""
        update = IssueUpdate(status=IssueStatus.ZAMKNIETY)
        assert update.status == IssueStatus.ZAMKNIETY

    def test_blad_gdy_tytul_za_krotki(self) -> None:
        """IssueUpdate z tytułem < 3 znaki powinno rzucić ValidationError."""
        with pytest.raises(ValidationError):
            IssueUpdate(title="AB")

    def test_model_dump_exclude_unset(self) -> None:
        """model_dump z exclude_unset=True powinno zawierać tylko ustawione pola."""
        update = IssueUpdate(title="Nowy tytuł", status=IssueStatus.W_TOKU)
        data = update.model_dump(exclude_unset=True)
        # Tylko title i status powinny być w słowniku
        assert set(data.keys()) == {"title", "status"}


# ---------------------------------------------------------------------------
# Testy IssueRead
# ---------------------------------------------------------------------------

class TestIssueRead:
    """Testy schematu odpowiedzi API."""

    def test_tworzy_z_slownika(self) -> None:
        """IssueRead powinno poprawnie zmapować dane ze słownika."""
        data = {
            "id": 1,
            "title": "Testowe",
            "description": "Opis",
            "status": "Nowy",
            "priority": "Średni",
            "author_id": "sub-001",
            "author_name": "Jan",
            "assignee_id": None,
            "assignee_name": None,
            "created_at": None,
            "updated_at": None,
        }
        issue = IssueRead(**data)
        assert issue.id == 1
        assert issue.title == "Testowe"
        assert issue.status == "Nowy"

    def test_from_attributes_z_obiektu_sqlalchemy(self, db_session, sample_issue) -> None:
        """IssueRead.model_validate powinno działać bezpośrednio na obiekcie SQLAlchemy."""
        issue_read = IssueRead.model_validate(sample_issue)
        assert issue_read.id == sample_issue.id
        assert issue_read.title == sample_issue.title
        assert issue_read.author_id == sample_issue.author_id

    def test_opcjonalne_pola_jako_none(self) -> None:
        """IssueRead powinno zaakceptować None w opcjonalnych polach."""
        issue = IssueRead(
            id=2,
            title="Issue bez detali",
            description=None,
            status="Nowy",
            priority="Niski",
            author_id=None,
            author_name=None,
            assignee_id=None,
            assignee_name=None,
            created_at=None,
            updated_at=None,
        )
        assert issue.description is None
        assert issue.author_id is None
