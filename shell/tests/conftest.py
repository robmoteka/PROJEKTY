"""
Globalna konfiguracja pytest dla modułu shell.

Ten plik jest automatycznie ładowany przez pytest.
Zawiera konfigurację asyncio i ewentualne fixtures wielokrotnego użytku.
"""
import pytest


# Konfiguracja pętli asyncio dla wszystkich testów async w tym module
def pytest_configure(config: pytest.Config) -> None:
    """Konfiguracja pytest — rejestracja markera asyncio."""
    config.addinivalue_line(
        "markers",
        "asyncio: oznacza test jako asynchroniczny (obsługiwany przez pytest-asyncio)",
    )
