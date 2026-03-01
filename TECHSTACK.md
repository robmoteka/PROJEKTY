# IT Project OS — Stos Technologiczny (Tech Stack)

> Ten plik jest jedynym źródłem prawdy o wszystkich technologiach, wersjach i narzędziach
> używanych w projekcie IT Project OS. Aktualizuj go przy każdej zmianie zależności.

---

## 🐍 Backend

| Technologia         | Wersja / Zakres   | Rola                                      |
|----------------------|--------------------|--------------------------------------------|
| Python               | 3.11+              | Język główny backendu                      |
| FastAPI              | ≥ 0.110.0          | Framework HTTP (Shell + moduły)            |
| Uvicorn              | ≥ 0.27.0           | Serwer ASGI                                |
| Jinja2               | ≥ 3.1.3            | Silnik szablonów HTML (partiale HTMX)      |
| SQLAlchemy           | ≥ 2.0.28           | ORM / warstwa dostępu do danych            |
| Alembic              | ≥ 1.13.1           | Migracje schematu bazy danych              |
| psycopg2-binary      | ≥ 2.9.9            | Sterownik PostgreSQL                       |
| python-dotenv        | ≥ 1.0.1            | Ładowanie zmiennych środowiskowych z .env  |

## 🌐 Frontend

| Technologia   | Wersja   | Rola                                           |
|----------------|----------|-------------------------------------------------|
| HTMX           | 2.0      | Silnik interakcji UI (swap HTML, AJAX)          |
| Tailwind CSS   | 3.x      | Framework CSS (utility-first)                   |
| DaisyUI        | 4.x      | Biblioteka komponentów UI na bazie Tailwind     |

## 🗄️ Baza danych

| Technologia   | Wersja        | Rola                        |
|----------------|---------------|-----------------------------|
| PostgreSQL     | 15 (Alpine)   | Główna baza danych systemu  |
> **Konwencja schematów:** każdy moduł ma własny schemat PostgreSQL (`shell`, `issues`, `kanban`, …).
> Tabele aplikacji nigdy nie trafiają do schematu `public`. Keycloak używa schematu `keycloak`.
## 🔐 Autentykacja / SSO

| Technologia       | Rola                                        |
|--------------------|---------------------------------------------|
| OIDC (OpenID Connect) | Protokół autentykacji                    |
| Keycloak / Azure AD   | Provider tożsamości (Identity Provider)  |
| BFF Pattern            | Bezpieczne zarządzanie sesją (HttpOnly cookies) |

## 🐳 Infrastruktura i DevOps

| Technologia       | Wersja / Obraz       | Rola                                         |
|--------------------|----------------------|-----------------------------------------------|
| Docker             | —                    | Konteneryzacja usług                          |
| Docker Compose     | 3.8                  | Orkiestracja środowiska wielokontenerowego    |
| Nginx              | Alpine               | Reverse proxy / brama (gateway)               |

## 🛠️ Narzędzia DB (UI)

| Narzędzie      | Port   | Rola                                     |
|-----------------|--------|------------------------------------------|
| pgAdmin 4       | 5080   | Oficjalne narzędzie administracji PG     |
| Adminer         | 5081   | Lekki interfejs webowy do bazy danych    |
| CloudBeaver     | 5082   | Webowa wersja DBeaver (multi-DB UI)      |

## 🧪 Testowanie

| Technologia            | Rola                                              |
|-------------------------|---------------------------------------------------|
| Pytest                  | Testy jednostkowe i integracyjne                  |
| httpx (AsyncClient)     | Testy integracyjne endpointów FastAPI             |
| Playwright / Cypress    | Testy E2E (scenariusze użytkownika, HTMX swap)   |

## 🔧 Jakość kodu

| Narzędzie   | Rola                                  |
|--------------|---------------------------------------|
| mypy         | Statyczna analiza typów Python        |
| ruff         | Linter i formatter kodu Python        |

## 📦 Porty serwisów

| Serwis            | Port wewnętrzny | Port zewnętrzny | Uwagi                     |
|--------------------|------------------|------------------|----------------------------|
| Nginx Gateway      | 80               | 5050             | Główne wejście do systemu  |
| Shell              | 8000             | — (via Nginx)    | Proxy: `/`                 |
| Module Issues      | 8000             | — (via Nginx)    | Proxy: `/modules/issues/`  |
| PostgreSQL         | 5432             | 5432             | Baza danych                |
| pgAdmin            | 80               | 5080             | UI bazy danych             |
| Adminer            | 8080             | 5081             | UI bazy danych             |
| CloudBeaver        | 8978             | 5082             | UI bazy danych             |
