/**
 * Testy E2E nawigacji — IT Project OS
 *
 * Sprawdzają zachowanie HTMX swap, nawigację mobilną i obsługę plików statycznych.
 * Wymagają działającego środowiska Docker (docker-compose up).
 */

import { test, expect, devices } from "@playwright/test";

// Adres bramy Nginx (zgodnie z docker-compose.yml: port 5050)
const BASE_URL = process.env.BASE_URL || "http://localhost:5050";

test.describe("Nawigacja — desktop", () => {
  test("strona główna zawiera element #main-content", async ({ page }) => {
    // Weryfikacja obecności kontenera docelowego HTMX
    await page.goto(BASE_URL);
    await expect(page.locator("#main-content")).toBeVisible();
  });

  test("klik w 'Issues' podmienia zawartość #main-content (HTMX swap)", async ({
    page,
  }) => {
    await page.goto(BASE_URL);

    // Zapamiętanie początkowego HTML kontenera
    const contentBefore = await page.locator("#main-content").innerHTML();

    // Klik w przycisk nawigacyjny Issues (desktop menu)
    await page.locator(".navbar-center button:has-text('Issues')").click();

    // Oczekiwanie na zakończenie wymiany przez HTMX
    await page.waitForFunction(() => {
      return !document.body.classList.contains("htmx-request");
    });

    const contentAfter = await page.locator("#main-content").innerHTML();

    // Zawartość powinna się zmienić po swap
    expect(contentAfter).not.toBe(contentBefore);
  });

  test("nawigacja HTMX aktualizuje URL w pasku adresu (hx-push-url)", async ({
    page,
  }) => {
    await page.goto(BASE_URL);

    // Klik w Issues — powinien zaktualizować URL
    await page.locator(".navbar-center button:has-text('Issues')").click();
    await page.waitForURL(`${BASE_URL}/modules/issues/**`);

    expect(page.url()).toContain("/modules/issues/");
  });

  test("wskaźnik ładowania #htmx-loading istnieje w DOM", async ({ page }) => {
    await page.goto(BASE_URL);
    // Wskaźnik renderowany w base.html — zawsze dostępny
    await expect(page.locator("#htmx-loading")).toBeAttached();
  });
});

test.describe("Nawigacja — mobile (375px)", () => {
  // Emulacja urządzenia mobilnego iPhone SE
  test.use({ viewport: { width: 375, height: 667 } });

  test("hamburger menu jest widoczne na mobile", async ({ page }) => {
    await page.goto(BASE_URL);

    // Przycisk hamburger (dropdown lg:hidden) — widoczny tylko na mobile
    const hamburger = page.locator(".navbar-start .dropdown.lg\\:hidden label");
    await expect(hamburger).toBeVisible();
  });

  test("desktop menu jest ukryte na mobile", async ({ page }) => {
    await page.goto(BASE_URL);

    // Menu desktopowe ukryte przez Tailwind 'hidden lg:flex'
    const desktopMenu = page.locator(".navbar-center.hidden.lg\\:flex");
    await expect(desktopMenu).toBeHidden();
  });

  test("klik w hamburger otwiera menu mobilne z Issues", async ({ page }) => {
    await page.goto(BASE_URL);

    // Otwórz dropdown przez klik na hamburger
    await page.locator(".navbar-start .dropdown.lg\\:hidden label").click();

    // Sprawdź, że element Issues jest widoczny w rozwiniętym menu
    const issuesBtn = page.locator(
      ".navbar-start .dropdown.lg\\:hidden ul button:has-text('Issues')"
    );
    await expect(issuesBtn).toBeVisible();
  });

  test("klik Issues z menu mobilnego podmienia #main-content", async ({
    page,
  }) => {
    await page.goto(BASE_URL);
    await page.locator(".navbar-start .dropdown.lg\\:hidden label").click();
    await page
      .locator(
        ".navbar-start .dropdown.lg\\:hidden ul button:has-text('Issues')"
      )
      .click();

    // Po kliknięciu URL powinien przejść na /modules/issues/
    await page.waitForURL(`${BASE_URL}/modules/issues/**`);
    expect(page.url()).toContain("/modules/issues/");
  });
});

test.describe("Pliki statyczne — Nginx", () => {
  test("GET /static/js/htmx.min.js zwraca 200", async ({ request }) => {
    const response = await request.get(`${BASE_URL}/static/js/htmx.min.js`);
    expect(response.status()).toBe(200);
    // Weryfikacja Content-Type
    expect(response.headers()["content-type"]).toContain("javascript");
  });

  test("GET /static/css/custom.css zwraca 200", async ({ request }) => {
    const response = await request.get(`${BASE_URL}/static/css/custom.css`);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toContain("css");
  });
});
