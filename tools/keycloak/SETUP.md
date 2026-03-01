# Konfiguracja Keycloak — kroki ręczne

Użyj tego przewodnika wenn automatyczny import (`--import-realm`) nie zadziała.

## Wymagania wstępne

Uruchomiony stack Docker:
```bash
docker compose up -d postgres keycloak
```

Poczekaj ~30 sekund na start Keycloak, następnie otwórz: **http://localhost:8080**

---

## Krok 1 — Zaloguj się do panelu admina

- URL: http://localhost:8080/admin
- Login: `admin`
- Hasło: `admin` (lub wartość z `.env`: `KEYCLOAK_ADMIN_PASSWORD`)

---

## Krok 2 — Utwórz Realm

1. Kliknij dropdown `master` w lewym górnym rogu
2. Wybierz **Create realm**
3. Ustaw:
   - **Realm name:** `it-os`
   - **Display name:** `IT Project OS`
4. Kliknij **Create**

---

## Krok 3 — Utwórz Client

1. W menu lewym: **Clients** → **Create client**
2. Ogólne:
   - **Client type:** `OpenID Connect`
   - **Client ID:** `it-project-os`
3. Capability config:
   - **Client authentication:** ON (tryb confidential)
   - **Standard flow:** ON
   - **Direct access grants:** OFF
4. Login settings:
   - **Valid redirect URIs:** `http://localhost:5050/auth/callback`
   - **Web origins:** `http://localhost:5050`
   - **Post logout redirect URIs:** `http://localhost:5050/`
5. Kliknij **Save**

### Skopiuj Client Secret

W zakładce **Credentials** skopiuj `Client secret` i wklej do `.env`:
```env
OIDC_CLIENT_SECRET=<skopiowana wartość>
```

---

## Krok 4 — Mapowanie ról w tokenie

1. W kliencie `it-project-os` → zakładka **Client scopes**
2. Kliknij na `it-project-os-dedicated`
3. **Add mapper** → **By configuration** → `User Realm Role`
4. Ustaw:
   - **Name:** `roles`
   - **Token Claim Name:** `roles`
   - **Claim JSON Type:** `String`
   - **Add to ID token:** ON
   - **Add to access token:** ON
5. Kliknij **Save**

---

## Krok 5 — Utwórz Role

1. Menu lewe: **Realm roles** → **Create role**
2. Dodaj kolejno:
   - `admin` — Pełny dostęp do systemu
   - `developer` — Dostęp do modułów roboczych
   - `viewer` — Tylko odczyt

---

## Krok 6 — Utwórz użytkowników testowych

### testuser (developer)
1. Menu lewe: **Users** → **Create new user**
2. Dane:
   - **Username:** `testuser`
   - **Email:** `test@example.com`
   - **First name:** `Test` / **Last name:** `User`
   - **Email verified:** ON
3. Zakładka **Credentials** → **Set password** → `test123` (temporary: OFF)
4. Zakładka **Role mapping** → **Assign role** → `developer`

### admin user
1. **Username:** `admin-app` (nie mylić z Keycloak adminem!)
2. **Email:** `admin@example.com`
3. Hasło: `admin123`
4. Role: `admin`, `developer`

---

## Weryfikacja

```bash
# Sprawdź discovery endpoint
curl http://localhost:8080/realms/it-os/.well-known/openid-configuration | jq .issuer

# Oczekiwany wynik:
# "http://localhost:8080/realms/it-os"
```

Jeśli issuer zgadza się z `OIDC_ISSUER` w `.env`, konfiguracja jest poprawna.

---

## Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---------|-------------|
| Keycloak nie startuje | Sprawdź logi: `docker compose logs keycloak` |
| Import realm failed | Sprawdź plik `realm-export.json`, uruchom ponownie z `docker compose restart keycloak` |
| 401 po zalogowaniu | Sprawdź `OIDC_CLIENT_SECRET` w `.env` — musi zgadzać się z wartością w Keycloak |
| Issuer mismatch | Sprawdź `KC_HOSTNAME_URL=http://localhost:8080` w docker-compose.yml |
| Shell nie może połączyć się z Keycloak | Sprawdź `extra_hosts: localhost:host-gateway` w serwisie shell |
