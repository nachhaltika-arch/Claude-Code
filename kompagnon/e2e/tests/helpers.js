/**
 * Gemeinsame Hilfen fuer die Browser-Tests.
 *
 * Die Zugangsdaten stammen aus kompagnon/backend/tests/seed_e2e.py und gelten
 * ausschliesslich fuer Testumgebungen.
 */
const E2E_EMAIL = 'e2e-admin@kompagnon.local';
const E2E_PASSWORD = 'e2e-test-passwort';
const E2E_COMPANY = 'E2E Testbetrieb Heizung GmbH';

/** Meldet sich an und wartet, bis das Dashboard steht. */
async function anmelden(page) {
  await page.goto('/login');
  await page.getByPlaceholder('ihre@email.de').fill(E2E_EMAIL);
  await page.locator('input[type="password"]').fill(E2E_PASSWORD);
  await page.getByRole('button', { name: /Anmelden/ }).click();
  await page.waitForURL(/\/app\//, { timeout: 20_000 });
}

/**
 * Sammelt Konsolenfehler waehrend eines Tests.
 * Rueckgabe: Funktion, die die bisher aufgelaufenen Fehler liefert.
 */
function konsoleBeobachten(page) {
  const fehler = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') fehler.push(msg.text());
  });
  page.on('pageerror', (err) => fehler.push(`Uncaught: ${err.message}`));

  return () => fehler;
}

module.exports = { E2E_EMAIL, E2E_PASSWORD, E2E_COMPANY, anmelden, konsoleBeobachten };
