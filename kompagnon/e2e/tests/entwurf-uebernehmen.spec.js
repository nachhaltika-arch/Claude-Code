const { test, expect } = require('@playwright/test');
const { E2E_COMPANY, anmelden } = require('./helpers');

/**
 * Der Weg von der Design-Vorschau auf die Seite.
 *
 * Bis zum 2026-08-13 endete der Zweig Sitemap → Wireframe → Style-Guide in
 * einem Bild auf dem Schirm: Die Vorschau baute Blöcke und Marken-CSS
 * zusammen, schrieb es aber nirgendwo hin. Ausgeliefert wurde etwas anderes,
 * das über `mockup_html` in GrapesJS kommt. Seither schreibt „Auf die Seite
 * übernehmen" genau dorthin — und dieser Test prüft, dass es ankommt.
 */
const API = process.env.E2E_API_URL
  || (process.env.E2E_BASE_URL || 'http://localhost:3000').replace(':3000', ':8000');

async function alsAngemeldet(page, pfad, optionen = {}) {
  const token = await page.evaluate(() => localStorage.getItem('kompagnon_token'));
  return page.request.fetch(`${API}${pfad}`, {
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    failOnStatusCode: false,
    ...optionen,
  });
}

async function seitenListe(page, leadId) {
  const antwort = await (await alsAngemeldet(page, `/api/sitemap/${leadId}`)).json();
  return Array.isArray(antwort) ? antwort : antwort.pages || [];
}

// Der Editor gibt nur den nächsten Schritt nach der letzten lückenlosen Kette
// frei. Für die Design-Ansicht müssen die Schritte davor bestätigt sein — der
// Seed bringt das Projekt nur bis Phase 1.
const SCHRITTE_BIS_DESIGN = [
  'briefing-unternehmen', 'audit', 'content-vollanalyse', 'briefing-website',
  'zugangsdaten', 'sitemap-ki', 'wireframe-ki', 'style-guide',
];

async function schritteBestaetigen(page, projektId) {
  for (const schritt of SCHRITTE_BIS_DESIGN) {
    // eslint-disable-next-line no-await-in-loop
    await alsAngemeldet(page, `/api/projects/${projektId}/confirm-step`, {
      method: 'POST', data: { step_id: schritt },
    });
  }
}

/** Der Style-Guide muss freigegeben sein, sonst ist die Design-Ansicht gesperrt. */
async function styleGuideFreigeben(page, projektId, freigegeben) {
  // Aus dem Wireframe-Endpunkt lesen, nicht aus dem Projekt: `GET /projects/{id}`
  // liefert `wireframe_data` nicht mit, und ein POST mit dem leeren Rest
  // loescht die Blöcke des Seeds — genau das ist beim Schreiben dieses Tests
  // einmal passiert.
  const daten = await (await alsAngemeldet(page,
    `/api/projects/${projektId}/wireframe`)).json();
  await alsAngemeldet(page, `/api/projects/${projektId}/wireframe`, {
    method: 'POST',
    data: { ...(daten || {}), style_guide_approved: freigegeben },
  });
}

test.describe('Entwurf auf die Seite übernehmen', () => {
  let projektId;
  let leadId;
  let seitenId;

  test.beforeEach(async ({ page }) => {
    page.on('dialog', (d) => d.accept());
    await anmelden(page);

    const projekte = await (await alsAngemeldet(page, '/api/projects')).json();
    const projekt = (Array.isArray(projekte) ? projekte : projekte.items || [])[0];
    projektId = projekt.id;
    leadId = projekt.lead_id;
    await styleGuideFreigeben(page, projektId, true);
    await schritteBestaetigen(page, projektId);

    seitenId = (await seitenListe(page, leadId))[0]?.id;
  });

  test.afterEach(async ({ page }) => {
    // Den Seed so hinterlassen, wie er vorgefunden wurde — die anderen Tests
    // prüfen den Fortschrittsstand. Die bestätigten Schritte bleiben stehen:
    // Dafür gibt es keinen Gegenendpunkt, und sie schalten nur Ansichten frei,
    // die kein anderer Test prüft.
    if (seitenId) {
      await alsAngemeldet(page, `/api/sitemap/pages/${seitenId}`, {
        method: 'PUT', data: { mockup_html: '' },
      });
    }
    if (projektId) await styleGuideFreigeben(page, projektId, false);
  });

  test('die Vorschau landet als Entwurf auf der Seite', async ({ page }) => {
    await page.getByRole('button', { name: 'Projekte' }).first().click();
    await page.getByRole('link', { name: /Alle Projekte/i }).or(
      page.getByRole('button', { name: /Alle Projekte/i }),
    ).first().click();
    await page.getByText(E2E_COMPANY).click();
    // Der View-Umschalter links („Ansicht"), nicht die gleichnamige
    // Phasen-Gruppe weiter unten in derselben Leiste.
    await page.getByRole('button', { name: 'Design', exact: true }).first().click();

    const uebernehmen = page.getByRole('button', { name: /Auf die Seite übernehmen/ });
    await expect(uebernehmen).toBeEnabled();
    await uebernehmen.click();

    await expect(page.getByText(/Übernommen/)).toBeVisible();

    // Nicht die Meldung zählt, sondern was in der Seite steht.
    const seiten = await seitenListe(page, leadId);
    const gespeichert = seiten.find((s) => s.id === seitenId)?.mockup_html || '';
    expect(gespeichert).toContain('data-block');
    expect(gespeichert).toContain('<style>');
  });
});
