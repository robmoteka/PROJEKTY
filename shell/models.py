"""
Modele ORM aplikacji Shell.

Zawiera modele SQLAlchemy reprezentujące tabele bazy danych:
- UserSession: sesje zalogowanych użytkowników (server-side session store)
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from db import Base


class UserSession(Base):
    """
    Model sesji użytkownika przechowywany po stronie serwera (PostgreSQL).

    Cookie przeglądarki zawiera tylko losowy `session_id` — dane tożsamości
    i tokeny OIDC nigdy nie opuszczają serwera (wzorzec BFF).
    """

    __tablename__ = "sessions"

    # Klucz główny tabeli
    id = Column(Integer, primary_key=True, index=True)
    # Losowy identyfikator sesji przechowywany w cookie HttpOnly
    session_id = Column(String, unique=True, index=True, nullable=False)
    # Identyfikator użytkownika (claim `sub` z OIDC)
    user_id = Column(String, index=True, nullable=False)
    # Adres e-mail użytkownika
    email = Column(String, nullable=True)
    # Imię i nazwisko użytkownika
    name = Column(String, nullable=True)
    # Login użytkownika (preferred_username z OIDC)
    preferred_username = Column(String, nullable=True)
    # Oryginalny id_token potrzebny jako hint przy wylogowaniu z OIDC
    id_token = Column(Text, nullable=True)
    # Czas utworzenia sesji (ustawiany automatycznie przez bazę danych)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    # Czas wygaśnięcia sesji (walidowany przy każdym żądaniu)
    expires_at = Column(DateTime, nullable=False)
