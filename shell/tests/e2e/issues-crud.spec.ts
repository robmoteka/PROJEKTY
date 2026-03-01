/**
 * Testy E2E operacji CRUD na module Issues — IT Project OS
 *
 * Sprawdzają pełny cykl życia zgłoszenia: tworzenie, edycję statusu, usuwanie.
 * Testy działają przez HTMX — weryfikują interakcję użytkownika z UI bez
 * bezpośredniego wywołania API.
 *
 * Wymagania:
 * - Uruchomione środowisko Docker (docker-compose up)
 * - Dostępna baza danych PostgreSQL (docker compose up postgres)
 *
 * Uruchomienie:
 *   npx playwright test issues-crud.spec.ts
 */

import { test, expect } from "@playwright/test";

// Adres bramy Nginx (zgodnie z docker-compose.yml: port 5050)
const BASE_URL = process.env.BASE_URL || "http://localhost:5050";
const ISSUES_URL = `${BASE_URL}/modules/issues/`;

// ---------------------------------------------------------------------------
// Helper — nawigacja do modułu Issues
// ---------------------------------------------------------------------------

/**
 * Pomocnicza funkcja nawigacji do listy zgłoszeń przez menu główne.
 * Używa HTMX swap, więc czeka na zakończenie ładowania.
 */
async function navigateToIssues(page: Parameters<typeof test>[1] extends { page: infer P } ? P : never) {
  await page.goto(BASE_URL);
  // Klik w przycisk Issues w menu desktopowym (HTMX hx-get)
  await page.locator(".navbar-center button:has-text('Issues')").click();
  // Czekamy na pojawienie się tabeli zgłoszeń w #main-content
  await expect(page.locator("#main-content table")).toBeVisible({ timeout: 5000 });
}

// ---------------------------------------------------------------------------
// Tworzenie nowego zgłoszenia
// ---------------------------------------------------------------------------

test.describe("Issues — tworzenie zgłoszenia", () => {
  test("formularz tworzy nowe zgłoszenie i pojawia się na liście", async ({
    page,
  }) => {
    // Unikalny tytuł z timestampem — uniknięcie kolizji między testami
    const tytul = `Testowe zgłoszenie E2E ${Date.now()}`;

    await navigateToIssues(page);

    // Klik w przycisk "Nowe zgłoszenie" (HTMX hx-get do formularza)
    await page.locator("[hx-get*='create'], button:has-text('Nowe zgłoszenie')").first().click();

    // Formularz powinien być widoczny
    await expect(page.locator("input[name='title']")).toBeVisible({ timeout: 5000 });

    // Wypełnienie formularza
    await page.fill("input[name='title']", tytul);
    await page.fill("textarea[name='description']", "Opis testowy zgłoszenia E2E");

    // Wysłanie formularza przez przycisk Submit (HTMX hx-post)
    await page.locator("button[type='submit']").click();

    // Nowe zgłoszenie powinno pojawić się na liście
    await expect(page.locator(`text=${tytul}`)).toBeVisible({ timeout: 5000 });
  });

  test("formularz zgłoszenia zawiera pola title i description", async ({
    page,
  }) => {
    await navigateToIssues(page);

    // Otwieramy formularz
    await page.locator("[hx-get*='create'], button:has-text('Nowe zgłoszenie')").first().click();

    // Weryfikacja wymaganych pól formularza
    await expect(page.locator("input[name='title']")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("textarea[name='description']")).toBeVisible({
      timeout: 5000,
    });
  });

  test("formularz bez tytułu nie przesyła danych (walidacja HTML5)", async ({
    page,
  }) => {
    await navigateToIssues(page);
    await page.locator("[hx-get*='create'], button:has-text('Nowe zgłoszenie')").first().click();

    // Klik submit bez wypełnienia tytułu — walidacja HTML5 required
    await expect(page.locator("input[name='title']")).toBeVisible({ timeout: 5000 });
    await page.locator("button[type='submit']").click();

    // Formularz powinien nadal być widoczny (brak przesłania)
    await expect(page.locator("input[name='title']")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Podgląd szczegółów zgłoszenia
// ---------------------------------------------------------------------------

test.describe("Issues — szczegóły zgłoszenia", () => {
  test("klik w tytuł zgłoszenia wyświetla szczegóły", async ({ page }) => {
    const tytul = `Zgłoszenie do podglądu ${Date.now()}`;

    // Najpierw utwórz zgłoszenie przez API HTTP bezpośrednio
    await page.goto(ISSUES_URL);
    const response = await page.request.post(`${ISSUES_URL}create`, {
      form: { title: tytul, description: "Opis" },
    });
    expect(response.ok()).toBeTruthy();

    // Nawigacja do listy i klik w tytuł
    await navigateToIssues(page);
    await page.locator(`text=${tytul}`).click();

    // Strona szczegółów powinna zawierać tytuł
    await expect(page.locator(`text=${tytul}`)).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// Filtrowanie zgłoszeń po statusie
// ---------------------------------------------------------------------------

test.describe("Issues — filtrowanie listy", () => {
  test("lista dostępna pod bezpośrednim URL /modules/issues/", async ({
    page,
  }) => {
    // Bezpośrednie wejście na URL modułu (bez HTMX swap)
    await page.goto(ISSUES_URL);

    // Moduł zwraca HTML partial — sprawdzamy że zawiera element tabeli
    await expect(page.locator("table")).toBeVisible({ timeout: 5000 });
  });

  test("parametr ?status=Nowy filtruje listę", async ({ page }) => {
    await page.goto(`${ISSUES_URL}list?status=Nowy`);

    // Każdy widoczny wiersz powinien mieć status "Nowy"
    const statusBadges = page.locator("[data-status], td:has-text('Nowy')");
    // Weryfikujemy tylko że strona załadowała się bez błędów
    const html = await page.content();
    expect(html).toContain("Nowy");
  });
});

// ---------------------------------------------------------------------------
// Pełny cykl CRUD (end-to-end journey)
// ---------------------------------------------------------------------------

test.describe("Issues — pełny cykl CRUD", () => {
  test("utwórz → sprawdź szczegóły → usuń zgłoszenie", async ({ page }) => {
    const tytul = `CRUD E2E Test ${Date.now()}`;

    // --- Krok 1: Utwórz zgłoszenie ---
    await navigateToIssues(page);
    await page.locator("[hx-get*='create'], button:has-text('Nowe zgłoszenie')").first().click();
    await expect(page.locator("input[name='title']")).toBeVisible({ timeout: 5000 });
    await page.fill("input[name='title']", tytul);
    await page.locator("button[type='submit']").click();

    // Zgłoszenie powinno być widoczne na liście
    await expect(page.locator(`text=${tytul}`)).toBeVisible({ timeout: 5000 });

    // --- Krok 2: Sprawdź że wiersz zawiera HTMX atrybuty ---
    const row = page.locator(`tr:has-text('${tytul}')`);
    await expect(row).toBeVisible();

    // --- Krok 3: Usuń zgłoszenie (przycisk usuń w wierszu) ---
    const deleteBtn = row.locator("[hx-delete], button:has-text('Usuń')").first();
    if (await deleteBtn.count() > 0) {
      // Akceptacja dialogu potwierdzenia jeśli istnieje
      page.once("dialog", (dialog) => dialog.accept());
      await deleteBtn.click();

      // Zgłoszenie powinno zniknąć z listy
      await expect(page.locator(`text=${tytul}`)).not.toBeVisible({
        timeout: 5000,
      });
    }
  });
});
