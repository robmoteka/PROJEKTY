# 🧪 Smoke Tests — Autentykacja OIDC

> Proste testy curl do weryfikacji działania endpointów autentykacji `/login` i `/logout`.
> Te testy sprawdzają podstawową dostępność endpointów i poprawność przekierowań.

---

## 📋 Wymagania wstępne

1. **Aplikacja działa lokalnie** (np. przez `docker-compose up` lub bezpośrednio przez Uvicorn)
2. **Nginx Gateway dostępny** na `http://localhost:5050`
3. **Keycloak uruchomiony** na `http://localhost:8080` (opcjonalnie - dla pełnego flow)

---

## 🔐 Test 1: Endpoint `/login`

Endpoint `/login` powinien przekierować użytkownika do Keycloak (authorization endpoint).

```bash
# Podstawowy test - sprawdzenie przekierowania (HTTP 302/307)
curl -i http://localhost:5050/auth/login

# Oczekiwany wynik:
# HTTP/1.1 302 Found (lub 307 Temporary Redirect)
# Location: http://localhost:8080/realms/it-os/protocol/openid-connect/auth?...
```

### Szczegóły:
- **Status HTTP:** `302 Found` lub `307 Temporary Redirect`
- **Header `Location`:** Powinien zawierać URL do Keycloak z parametrami:
  - `client_id=it-project-os`
  - `response_type=code`
  - `redirect_uri=http://localhost:5050/auth/callback`
  - `scope=openid+profile+email`
  - `state=...` (losowy token CSRF)

### Dodatkowy test (śledzenie przekierowania):
```bash
# Wyświetl pełny URL przekierowania
curl -i -L http://localhost:5050/auth/login 2>&1 | grep -i location

# Alternatywnie - pokaż tylko headers
curl -I http://localhost:5050/auth/login
```

---

## 🚪 Test 2: Endpoint `/logout`

Endpoint `/logout` powinien wyczyścić sesję użytkownika i przekierować na stronę główną lub Keycloak logout.

```bash
# Test 1: Logout bez aktywnej sesji (powinien przekierować na / lub zwrócić 200)
curl -i http://localhost:5050/auth/logout

# Oczekiwany wynik (w zależności od implementacji):
# - HTTP 302/307 → Location: /
# - LUB HTTP 200 + komunikat "Wylogowano pomyślnie"
```

### Test z aktywną sesją (zaawansowany):
```bash
# Krok 1: Utwórz ciasteczko sesyjne (przykładowe - w praktyce otrzymasz je po zalogowaniu)
SESSION_COOKIE="it_os_session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Krok 2: Wyloguj się używając sesji
curl -i -b "$SESSION_COOKIE" http://localhost:5050/auth/logout

# Oczekiwany wynik:
# - HTTP 302 → Location: / (lub Keycloak logout URL)
# - Set-Cookie: it_os_session=; Max-Age=0; (wyczyszczenie cookie)
```

---

## 🔍 Test 3: Callback endpoint (opcjonalny)

Endpoint `/auth/callback` obsługuje zwrotne przekierowanie z Keycloak po zalogowaniu.

```bash
# Test błędu - callback bez parametru "code" (powinien zwrócić błąd)
curl -i http://localhost:5050/auth/callback

# Oczekiwany wynik:
# HTTP 400 Bad Request
# {"detail": "Missing authorization code"}
```

---

## 🛠️ Debugging / Rozszerzone testy

### 1. Sprawdź headers i cookies:
```bash
# Pokaż wszystkie headers (w tym Set-Cookie)
curl -v http://localhost:5050/auth/login 2>&1 | grep -E "(< HTTP|< Location|< Set-Cookie)"
```

### 2. Test pełnego flow (manualny):
```bash
# 1. Otwórz przeglądarkę i przejdź do:
#    http://localhost:5050/auth/login
#
# 2. Zaloguj się w Keycloak (user: admin, password: admin)
#
# 3. Sprawdź, czy zostałeś przekierowany z powrotem do aplikacji
#
# 4. Wyloguj się:
#    http://localhost:5050/auth/logout
```

### 3. Weryfikacja Keycloak (czy działa):
```bash
# Sprawdź dostępność OpenID Discovery
curl -s http://localhost:8080/realms/it-os/.well-known/openid-configuration | jq .

# Oczekiwany wynik: JSON z konfiguracją OIDC (authorization_endpoint, token_endpoint, etc.)
```

---

## ✅ Checklist — Wyniki Smoke Testów

- [ ] `/auth/login` zwraca status 302/307 i przekierowuje do Keycloak
- [ ] URL przekierowania zawiera poprawne parametry (`client_id`, `redirect_uri`, `scope`)
- [ ] `/auth/logout` czyści sesję i przekierowuje na stronę główną
- [ ] Keycloak Discovery URL odpowiada poprawnym JSON-em
- [ ] Brak błędów 500 Internal Server Error na endpointach

---

## 📝 Notatki

- **BFF Pattern:** Sesja jest przechowywana w `HttpOnly` cookie, więc frontend nie ma bezpośredniego dostępu do tokena.
- **CSRF Protection:** Parametr `state` w OAuth2 flow chroni przed atakami CSRF.
- **Produkcja:** W środowisku produkcyjnym upewnij się, że:
  - Używasz `HTTPS` (nie `HTTP`)
  - `SESSION_SECRET_KEY` jest losowy i bezpieczny
  - Cookies mają flagę `Secure=True`
