import { test, expect } from '@playwright/test';

test.describe('Shell auth + HTMX flow', () => {
  test('po wejściu na stronę główną widoczny jest przycisk logowania', async ({ page }) => {
    await page.goto('http://localhost:5050/');
    await expect(page.getByRole('link', { name: 'Zaloguj przez SSO' })).toBeVisible();
  });

  test('nawigacja HTMX używa kontenera #main-content', async ({ page }) => {
    await page.goto('http://localhost:5050/');

    // Sprawdzamy, że główny kontener na partiale HTMX istnieje
    const mainContent = page.locator('#main-content');
    await expect(mainContent).toBeVisible();

    // Weryfikujemy, że przycisk Issues jest skonfigurowany pod HTMX
    const issuesButton = page.locator('[hx-get="/modules/issues/"]');
    await expect(issuesButton).toHaveAttribute('hx-target', '#main-content');
  });
});
