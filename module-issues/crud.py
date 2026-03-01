"""
Operacje CRUD dla modułu Issues.

Każda funkcja przyjmuje sesję SQLAlchemy jako pierwszy argument —
zarządzanie sesją (commit/rollback) należy do wywołującego (endpoint FastAPI).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models import Issue
from schemas import IssueCreate, IssueUpdate


def get_issues(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> list[Issue]:
    """
    Pobiera listę zgłoszeń z opcjonalnym filtrem statusu i paginacją.

    Args:
        db: Sesja SQLAlchemy przekazana przez FastAPI Depends.
        skip: Liczba rekordów do pominięcia (offset paginacji).
        limit: Maksymalna liczba zwracanych rekordów.
        status: Opcjonalny filtr — zwraca tylko zgłoszenia o podanym statusie.

    Returns:
        Lista obiektów Issue spełniających kryteria.
    """
    # Budujemy zapytanie bazowe — sortujemy od najnowszych
    query = db.query(Issue).order_by(Issue.created_at.desc())
    # Stosujemy filtr statusu jeśli podany
    if status is not None:
        query = query.filter(Issue.status == status)
    return query.offset(skip).limit(limit).all()


def get_issue_by_id(db: Session, issue_id: int) -> Issue | None:
    """
    Pobiera pojedyncze zgłoszenie po ID.

    Args:
        db: Sesja SQLAlchemy.
        issue_id: Identyfikator zgłoszenia.

    Returns:
        Obiekt Issue lub None jeśli nie istnieje.
    """
    return db.query(Issue).filter(Issue.id == issue_id).first()


def create_issue(
    db: Session,
    issue_data: IssueCreate,
    author_id: str,
    author_name: str,
) -> Issue:
    """
    Tworzy nowe zgłoszenie w bazie danych.

    Args:
        db: Sesja SQLAlchemy.
        issue_data: Zwalidowane dane wejściowe z formularza.
        author_id: Identyfikator autora (claim `sub` z OIDC lub nagłówek X-User-Sub).
        author_name: Czytelna nazwa autora (z nagłówka X-User-Name).

    Returns:
        Nowo utworzony obiekt Issue z wypełnionym ID.
    """
    # Tworzymy obiekt modelu z danych formularza
    db_issue = Issue(
        title=issue_data.title,
        description=issue_data.description,
        priority=issue_data.priority.value,
        assignee_id=issue_data.assignee_id,
        assignee_name=issue_data.assignee_name,
        author_id=author_id,
        author_name=author_name,
    )
    db.add(db_issue)
    db.commit()
    # Odświeżamy obiekt, żeby pobrać wygenerowane wartości (id, created_at, updated_at)
    db.refresh(db_issue)
    return db_issue


def update_issue(
    db: Session,
    issue_id: int,
    issue_data: IssueUpdate,
) -> Issue | None:
    """
    Aktualizuje zgłoszenie — partial update (tylko podane pola).

    Args:
        db: Sesja SQLAlchemy.
        issue_id: Identyfikator zgłoszenia do aktualizacji.
        issue_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt Issue lub None jeśli zgłoszenie nie istnieje.
    """
    # Pobieramy istniejące zgłoszenie
    db_issue = get_issue_by_id(db, issue_id)
    if db_issue is None:
        return None

    # Iterujemy po polach i aktualizujemy tylko te, które nie są None
    update_data = issue_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enum do wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_issue, field, value)

    db.commit()
    # Pobieramy zaktualizowany obiekt świeżym zapytaniem zamiast db.refresh
    # (unika problemów z wygaśniętą sesją po commit)
    return get_issue_by_id(db, issue_id)


def delete_issue(db: Session, issue_id: int) -> bool:
    """
    Usuwa zgłoszenie z bazy danych.

    Args:
        db: Sesja SQLAlchemy.
        issue_id: Identyfikator zgłoszenia do usunięcia.

    Returns:
        True jeśli zgłoszenie zostało usunięte, False jeśli nie istniało.
    """
    db_issue = get_issue_by_id(db, issue_id)
    if db_issue is None:
        return False
    db.delete(db_issue)
    db.commit()
    return True
