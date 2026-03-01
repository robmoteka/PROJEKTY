# IT Project OS — Uruchamianie testów

## Unit / Integration — Pytest (moduł `shell`)

### W kontenerze Docker (zalecane)

```bash
# Wszystkie testy
docker compose exec shell pytest

# Tylko unit testy
docker compose exec shell pytest tests/test_auth_unit.py tests/test_sessions_unit.py tests/test_db_unit.py -v

# Tylko integration testy
docker compose exec shell pytest tests/test_auth_integration.py tests/test_middleware_integration.py tests/test_sessions_integration.py -v

# Szczegółowy output z krótkim traceback
docker compose exec shell pytest --tb=short -v
```

### Lokalnie (venv)

```bash
cd shell
pip install -r requirements.txt
pytest -v
```

---

## E2E — Playwright (`shell/tests/e2e/`)

> Wymagają działającego stacku: `docker compose up -d`  
> Zmienna `BASE_URL` domyślnie wskazuje na `http://localhost:5050`

### Instalacja (jednorazowo)

```bash
npm init -y
npm install -D @playwright/test
npx playwright install chromium
```

### Uruchamianie

```bash
# Uruchom testy E2E nawigacji
npx playwright test shell/tests/e2e/navigation.spec.ts

# Z podglądem UI
npx playwright test shell/tests/e2e/navigation.spec.ts --ui

# Inny BASE_URL (np. staging)
BASE_URL=http://staging.example.com npx playwright test shell/tests/e2e/
```

---

## Struktura plików testowych

```
shell/tests/
├── conftest.py                    # Globalna konfiguracja pytest
├── test_auth_unit.py              # Unit: JWT, OIDC service
├── test_auth_integration.py       # Integration: endpointy /login, /callback, /logout
├── test_db_unit.py                # Unit: modele SQLAlchemy, schematy Pydantic
├── test_middleware_integration.py # Integration: middleware sesji
├── test_sessions_unit.py          # Unit: logika sesji
├── test_sessions_integration.py   # Integration: zapis/odczyt sesji w PostgreSQL
└── e2e/
    ├── auth-flow.spec.ts          # E2E: przepływ logowania OIDC
    └── navigation.spec.ts         # E2E: HTMX swap, hamburger menu, pliki statyczne
```
