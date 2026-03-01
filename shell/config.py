"""
Konfiguracja aplikacji Shell — zmienne środowiskowe ładowane z pliku .env.
Używa pydantic-settings do walidacji i typowania ustawień.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralne ustawienia aplikacji Shell ładowane z .env."""

    # --- Baza danych ---
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "secret"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "it_os_db"

    # --- OIDC Provider (Keycloak / Azure AD) ---
    OIDC_ISSUER: str = "http://localhost:8080/realms/it-os"
    OIDC_CLIENT_ID: str = "shell"
    OIDC_CLIENT_SECRET: str = "change-me"
    OIDC_REDIRECT_URI: str = "http://localhost:5050/callback"
    # Żądane zakresy uprawnień od OIDC providera
    OIDC_SCOPES: str = "openid profile email"

    # --- JWT / Sesja ---
    # Algorytm weryfikacji tokenu OIDC (RS256 dla Keycloak, HS256 dla prostych przypadków)
    JWT_ALGORITHM: str = "RS256"
    # Nazwa ciasteczka HttpOnly przechowującego sesję
    SESSION_COOKIE_NAME: str = "session"
    # Czas życia sesji w sekundach (1 godzina)
    SESSION_COOKIE_MAX_AGE: int = 3600
    # Klucz do podpisywania własnych tokenów sesji (jeśli używamy HS256)
    SECRET_KEY: str = "super-secret-change-in-production"

    # --- CORS ---
    # Lista dozwolonych origins oddzielonych przecinkami (dev: localhost z różnymi portami)
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
