"""
Konfiguracja SQLAlchemy — moduł Projekty.

Wykorzystuje Settings z config.py jako jedyne źródło prawdy
dla parametrów połączenia z bazą danych.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings


# Klasa bazowa dla modeli SQLAlchemy — nowy styl SQLAlchemy 2.0
class Base(DeclarativeBase):
    """Klasa bazowa dla wszystkich modeli SQLAlchemy w module Projekty."""

    pass


# Pobieramy ustawienia przez singleton — DATABASE_URL pochodzi z Settings
_settings = get_settings()

# Eksportujemy DATABASE_URL dla zgodności z alembic/env.py (importuje go bezpośrednio)
DATABASE_URL: str = _settings.DATABASE_URL

# Silnik SQLAlchemy — jedno połączenie współdzielone przez całą aplikację
engine = create_engine(DATABASE_URL)

# Fabryka sesji — autocommit=False wymaga jawnego commit()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency FastAPI — dostarcza sesję bazy danych dla pojedynczego requesta.

    Gwarantuje zamknięcie sesji nawet w przypadku wyjątku (blok finally).

    Yields:
        Aktywna sesja SQLAlchemy gotowa do użycia w endpoincie.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
