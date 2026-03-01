"""
Konfiguracja modułu Module Issues — zmienne środowiskowe ładowane z pliku .env.
Używa pydantic-settings do walidacji i typowania ustawień.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralne ustawienia modułu Module Issues ładowane z .env."""

    # --- Baza danych ---
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "secret"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "it_os_db"

    # Klucz do weryfikacji tokenów sesji (ten sam co w Shell)
    SECRET_KEY: str = "super-secret-change-in-production"

    # --- CORS ---
    # Lista dozwolonych origins oddzielonych przecinkami
    CORS_ORIGINS: str = "http://localhost:5050,http://localhost:8001,http://localhost:8002"

    model_config = SettingsConfigDict(
        # Plik .env względem katalogu głównego projektu
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignoruj dodatkowe zmienne, których nie ma w modelu
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        """Zwraca pełny URL połączenia z bazą danych PostgreSQL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Zwraca singleton konfiguracji (cache przez lru_cache).
    Użyj jako zależności FastAPI: Depends(get_settings).
    """
    return Settings()
