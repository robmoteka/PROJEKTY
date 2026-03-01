"""
Zależności FastAPI (Depends) używane w całej aplikacji Shell.

Zawiera zależności do wstrzykiwania:
- get_current_user: wyszukuje sesję użytkownika w bazie PostgreSQL na podstawie
  session_id z HttpOnly cookie — zwraca dane tożsamości lub None
- require_authenticated_user: guard wymagający zalogowania (HTTP 401 jeśli brak sesji)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config import Settings, get_settings
from db import get_db
from models import UserSession

logger = logging.getLogger(__name__)


async def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    session: Annotated[str | None, Cookie()] = None,
) -> dict[str, str] | None:
    """
    Wyszukuje dane aktualnie zalogowanego użytkownika na podstawie session_id.

    Odczytuje session_id z HttpOnly cookie, wyszukuje odpowiadający rekord
    UserSession w PostgreSQL i weryfikuje, czy sesja nie wygasła. Mechanizm
    sesji server-side pozwala na natychmiastowe unieważnienie sesji (usunięcie
    rekordu z DB) bez czekania na wygaśnięcie tokenu JWT.

    Args:
        settings: Ustawienia aplikacji (nazwa cookie sesji).
        db: Sesja bazy danych.
        session: Wartość HttpOnly cookie 'session' (session_id — NIE JWT!).

    Returns:
        Słownik z danymi użytkownika lub None jeśli nie zalogowany / sesja wygasła.
    """
    # Brak cookie = użytkownik niezalogowany
    if not session:
        return None

    # Wyszukujemy rekord sesji w bazie danych po session_id
    db_session: UserSession | None = (
        db.query(UserSession)
        .filter(UserSession.session_id == session)
        .first()
    )

    # Nie znaleziono sesji w DB — cookie może być stare lub sfałszowane
    if db_session is None:
        logger.warning("Nie znaleziono sesji w DB dla podanego cookie session_id.")
        return None

    # Sprawdzamy czy sesja nie wygasła — porównujemy z aktualnym czasem UTC
    now: datetime = datetime.now(timezone.utc)
    expires: datetime = db_session.expires_at
    # Normalizujemy do aware datetime jeśli baza zwróciła naive
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires <= now:
        # Sesja wygasła — usuwamy martwy rekord i traktujemy jak niezalogowany
        logger.info("Sesja wygasła dla user_id=%s — usuwam z DB.", db_session.user_id)
        db.delete(db_session)
        db.commit()
        return None

    # Sesja aktywna — zwracamy dane tożsamości użytkownika
    return {
        "sub": db_session.user_id,
        "email": db_session.email or "",
        "name": db_session.name or "",
        "preferred_username": db_session.preferred_username or "",
    }


async def require_authenticated_user(
    user: Annotated[dict[str, str] | None, Depends(get_current_user)],
) -> dict[str, str]:
    """
    Guard (zależność ochronna) — wymaga zalogowanego użytkownika.

    Użycie w routerze: `user: Annotated[dict, Depends(require_authenticated_user)]`

    Args:
        user: Dane użytkownika z get_current_user (None = niezalogowany).

    Returns:
        Słownik z danymi użytkownika (jeśli zalogowany).

    Raises:
        HTTPException 401: Gdy użytkownik nie jest zalogowany.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Musisz być zalogowany, aby uzyskać dostęp do tej strony.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
    return user
