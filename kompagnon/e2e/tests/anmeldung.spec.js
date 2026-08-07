const { test, expect } = require('@playwright/test');
const { E2E_EMAIL, E2E_PASSWORD, anmelden, konsoleBeobachten } = require('./helpers');

test.describe('Anmeldung und Sitzung', () => {
  test('Anmeldung führt ins Dashboard', async ({ page }) => {
    const fehler = konsoleBeobachten(page);

    await anmelden(page);

    await expect(page).toHaveURL(/\/app\/dashboard/);
    await expect(page.getByRole('heading', { name: /Dashboard/i }).first()).toBeVisible();
    expect(fehler(), 'Konsolenfehler beim Anmelden').toEqual([]);
  });

  test('Sitzung überlebt einen Reload', async ({ page }) => {
    await anmelden(page);

    await page.reload();

    // Kein Rücksprung auf die Anmeldeseite
    await expect(page).toHaveURL(/\/app\//);
    await expect(page.locator('input[type="password"]')).toHaveCount(0);
  });

  test('falsches Passwort wird abgewiesen', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('ihre@email.de').fill(E2E_EMAIL);
    await page.locator('input[type="password"]').fill('definitiv-falsch');
    await page.getByRole('button', { name: /Anmelden/ }).click();

    // Bleibt auf der Anmeldeseite
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('geschützte Seite ohne Anmeldung leitet zur Anmeldung', async ({ page }) => {
    await page.goto('/app/dashboard');

    await expect(page).toHaveURL(/\/login/);
  });
});
