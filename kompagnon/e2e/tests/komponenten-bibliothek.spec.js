const { test, expect } = require('@playwright/test');
const { anmelden, konsoleBeobachten } = require('./helpers');

/**
 * Regressionsschutz fuer den Fehler vom 2026-05-07: Die Route
 * /api/components/layout-presets stand hinter dem '/{slug}'-Catch-all und
 * lieferte 404. Das Frontend schluckte den Fehler, der Layout-Selector blieb
 * leer — drei Monate lang, ohne dass irgendwo etwas auffiel.
 *
 * Der Backend-Test prueft die Route. Dieser Test prueft, was der Nutzer sieht.
 */
test.describe('Komponenten-Bibliothek', () => {
  test.beforeEach(async ({ page }) => {
    await anmelden(page);
    // Die Bibliothek lag unter Einstellungen; seit dem 17.08.2026 steht sie
    // unter Verwaltung - was fuer alle gilt, getrennt von dem, was eine
    // Person fuer sich einstellt (UX-16).
    await page.getByRole('button', { name: 'Verwaltung' }).first().click();
    await page.getByRole('button', { name: 'Komponenten-Bibliothek' }).first().click();
    await expect(page).toHaveURL(/component-library/);
  });

  test('Bibliothek listet Komponenten', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Komponenten-Bibliothek/i })).toBeVisible();

    // Die Seed-Bibliothek bringt deutlich mehr als eine Handvoll Eintraege mit.
    await expect(page.getByText(/\d+ Eintraege/)).toBeVisible();
    await expect(page.getByText('cta-angebot')).toBeVisible();
  });

  test('Layout-Selector ist gefüllt', async ({ page }) => {
    const fehler = konsoleBeobachten(page);

    await page.getByRole('button', { name: /Mit KI generieren/ }).click();

    const selector = page.locator('select').filter({ hasText: 'Beliebig' });
    await expect(selector).toBeVisible();

    // Vor dem Fix enthielt die Auswahl nur den Standardeintrag.
    const optionen = await selector.locator('option').count();
    expect(optionen, 'Layout-Presets fehlen — /api/components/layout-presets erreichbar?').toBeGreaterThan(1);

    expect(fehler()).toEqual([]);
  });

  test('Kategoriewechsel tauscht die Layout-Vorschläge', async ({ page }) => {
    await page.getByRole('button', { name: /Mit KI generieren/ }).click();

    // Auf der Seite gibt es zwei Kategorie-Auswahlen: den Bibliotheksfilter
    // (Wert 'all') und die im Dialog (Wert 'HERO'). Ueber den Wert statt ueber
    // die Reihenfolge auswaehlen — sonst trifft der Test den Filter.
    const kategorie = page.getByRole('combobox').filter({ hasNotText: 'Alle Kategorien' })
      .filter({ hasText: 'HERO' }).first();
    const layout = page.locator('select').filter({ hasText: 'Beliebig' });

    await expect(kategorie).toHaveValue('HERO');

    const heroOptionen = await layout.locator('option').allTextContents();
    await kategorie.selectOption('CTA');

    // Optionen einer Auswahlliste gelten nicht als "sichtbar" — deshalb auf die
    // Inhaltsaenderung warten statt auf Sichtbarkeit.
    await expect
      .poll(() => layout.locator('option').allTextContents(), {
        message: 'Presets sind nicht kategorieabhängig',
      })
      .not.toEqual(heroOptionen);
  });
});
