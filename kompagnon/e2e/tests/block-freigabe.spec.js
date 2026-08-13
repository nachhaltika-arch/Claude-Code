const { test, expect } = require('@playwright/test');
const { anmelden } = require('./helpers');

/**
 * Der Weg eines unsauberen Blocks durch die Oberflaeche.
 *
 * Das Tor zur Bibliothek steht seit dem 2026-08-13 (Stufe A): Ein Block, der
 * den Vertrag verletzt, wird gespeichert, aber nicht freigegeben. Ohne
 * Oberflaeche war das eine stille Entscheidung — der Block verschwand aus dem
 * Wireframe-Editor und niemand erfuhr, warum. Dieser Test prueft genau das,
 * was der Nutzer sehen muss: den Entwurfs-Status, den Grund im Klartext, die
 * verweigerte Freigabe — und dass die Freigabe nach der Reparatur klappt.
 */
const NAME = 'E2E Vertragsprobe';
const SLUG = 'e2e-vertragsprobe';

// Der iframe schickt die Besucher-IP an Google, bevor jemand klickt — Regel R1.
const UNSAUBER = `<section data-block="${SLUG}" class="py-16">`
  + '<h2>Karte</h2>'
  + '<iframe src="https://www.google.com/maps/embed?pb=x"></iframe>'
  + '</section>';

const SAUBER = `<section data-block="${SLUG}" class="py-16">`
  + '<h2>Waermepumpe vom Meisterbetrieb</h2>'
  + '<p>Beratung, Foerderantrag und Einbau aus einer Hand.</p>'
  + '</section>';

/**
 * Raeumt den Probeblock ueber die API weg — vor *und* nach dem Test.
 *
 * Ueber die Oberflaeche aufzuraeumen waere von genau der Oberflaeche abhaengig,
 * die hier auf dem Pruefstand steht: bleibt ein Block liegen, vergibt die
 * Neuanlage beim naechsten Lauf `-2` als Slug, `data-block` passt nicht mehr
 * dazu — und der Test faellt an einer Stelle um, die mit seiner Frage nichts
 * zu tun hat.
 */
async function probeblockEntfernen(page) {
  const token = await page.evaluate(() => localStorage.getItem('kompagnon_token'));
  const basis = process.env.E2E_BASE_URL || 'http://localhost:3000';
  const api = process.env.E2E_API_URL || basis.replace(':3000', ':8000');

  for (const slug of [SLUG, `${SLUG}-2`, `${SLUG}-3`]) {
    await page.request.delete(`${api}/api/components/${slug}`, {
      headers: { Authorization: `Bearer ${token}` },
      failOnStatusCode: false,
    });
  }
}

/** Direktes goto auf /app/... landet nach dem Neuladen im Dashboard — die
 *  Bibliothek wird deshalb ueber die Navigation geoeffnet, wie ein Nutzer es tut. */
async function bibliothekOeffnen(page) {
  await page.getByRole('button', { name: 'Einstellungen' }).first().click();
  await page.getByRole('button', { name: 'Komponenten-Bibliothek' }).first().click();
  await expect(page).toHaveURL(/component-library/);
  await expect(page.getByRole('heading', { name: /Komponenten-Bibliothek/i })).toBeVisible();
}

/** Legt den Probeblock mit festem Slug an — nicht mit dem aus dem Namen
 *  abgeleiteten, damit ein Rest aus einem frueheren Lauf sofort auffaellt. */
async function probeblockAnlegen(page, html) {
  await page.getByRole('button', { name: /Neue Komponente/ }).click();
  await page.getByLabel('Slug').fill(SLUG);
  await page.getByLabel('Name').fill(NAME);
  await page.getByLabel('HTML-Template').fill(html);
  await page.getByRole('button', { name: 'Anlegen' }).click();
}

test.describe('Block-Freigabe', () => {
  test.beforeEach(async ({ page }) => {
    // Loeschen und Verwerfen fragen per window.confirm nach.
    page.on('dialog', (d) => d.accept());
    await anmelden(page);
    await probeblockEntfernen(page);
    await bibliothekOeffnen(page);
  });

  test.afterEach(async ({ page }) => {
    await probeblockEntfernen(page);
  });

  test('unsauberer Block landet als Entwurf, mit Grund und ohne Freigabe', async ({ page }) => {
    await probeblockAnlegen(page, UNSAUBER);

    // Der Status steht am Block, nicht nur im Log.
    await expect(page.getByText('Entwurf').first()).toBeVisible();

    // Und der Grund steht im Klartext — nicht als Regelnummer allein.
    await expect(page.getByText(/Vertrag verletzt/)).toBeVisible();
    await expect(page.getByText(/iframe.*nicht erlaubt/i)).toBeVisible();

    // Die Freigabe ist da, aber gesperrt.
    await expect(page.getByRole('button', { name: /Freigeben/ })).toBeDisabled();
  });

  test('nach der Reparatur ist die Freigabe moeglich', async ({ page }) => {
    await probeblockAnlegen(page, UNSAUBER);
    await expect(page.getByText(/Vertrag verletzt/)).toBeVisible();

    await page.getByLabel('HTML-Template').fill(SAUBER);
    await page.getByRole('button', { name: 'Speichern' }).click();

    const freigeben = page.getByRole('button', { name: /Freigeben/ });
    await expect(freigeben).toBeEnabled();
    await freigeben.click();

    await expect(page.getByText('Freigegeben').first()).toBeVisible();
    // Nach der Freigabe ist nichts mehr offen — der Kasten verschwindet.
    await expect(page.getByText(/Vertrag verletzt/)).toHaveCount(0);
  });
});
