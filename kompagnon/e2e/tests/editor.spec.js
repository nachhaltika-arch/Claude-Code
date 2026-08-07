const { test, expect } = require('@playwright/test');
const { E2E_COMPANY, anmelden, konsoleBeobachten } = require('./helpers');

/**
 * Der kritische Pfad im Online-Fertig-Editor.
 *
 * Voraussetzung ist das Seed aus backend/tests/seed_e2e.py: Es bringt ein
 * Projekt in einen Zustand, in dem Phase 1 lueckenlos abgeschlossen ist. Ohne
 * das sind Sitemap, Wireframe und Style Guide gesperrt — genau deshalb liess
 * sich dieser Teil bisher weder manuell noch automatisiert pruefen.
 */
test.describe('Online-Fertig-Editor', () => {
  test.beforeEach(async ({ page }) => {
    await anmelden(page);
    await page.getByRole('button', { name: 'Projekte' }).first().click();
    await page.getByRole('link', { name: /Alle Projekte/i }).or(
      page.getByRole('button', { name: /Alle Projekte/i })
    ).first().click();
    await expect(page).toHaveURL(/\/app\/projects/);
  });

  test('Seed-Projekt ist in der Liste', async ({ page }) => {
    await expect(page.getByText(E2E_COMPANY)).toBeVisible();
  });

  test('Editor öffnet und zeigt die vier Views', async ({ page }) => {
    await page.getByText(E2E_COMPANY).click();
    await expect(page).toHaveURL(/\/app\/projects\/\d+/);

    for (const view of ['Sitemap', 'Wireframe', 'Style Guide', 'Design']) {
      await expect(page.getByText(view, { exact: false }).first()).toBeVisible();
    }
  });

  test('Sitemap-View ist nicht gesperrt', async ({ page }) => {
    const fehler = konsoleBeobachten(page);

    await page.getByText(E2E_COMPANY).click();
    await page.getByText('SITEMAP', { exact: false }).first().click();

    // Die Sperrmeldung darf nicht erscheinen — sie war der Grund, warum der
    // manuelle Smoke-Test hier nicht weiterkam.
    await expect(page.getByText(/Schritt ist gesperrt/)).toHaveCount(0);
    expect(fehler()).toEqual([]);
  });

  test('Fortschrittsanzeige spiegelt den Seed-Stand', async ({ page }) => {
    await page.getByText(E2E_COMPANY).click();

    // Phase 1 ist im Seed abgeschlossen, der Zähler darf nicht bei 0 stehen.
    const fortschritt = page.getByText(/FORTSCHRITT/i).locator('..');
    await expect(fortschritt).not.toHaveText(/0\/17/);
  });
});
