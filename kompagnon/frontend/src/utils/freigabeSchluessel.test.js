/**
 * Die elf Freigaben stehen an zwei Stellen — die Schlüssel müssen gleich sein.
 *
 * **Warum sie doppelt stehen dürfen (26.08.2026, L-105).** `BriefingTab.jsx`
 * zeigt sie dem Innendienst, `Projektfreigaben.jsx` dem Kunden. Die
 * Beschriftung ist Sprache und darf sich unterscheiden — dem Kunden sagt man
 * anderes als dem eigenen Team. Der **Schlüssel** ist dagegen die Verbindung
 * zum Datensatz: Steht auf der einen Seite `abnahme_go_live` und auf der
 * anderen `abnahme`, dann gibt der Kunde etwas frei, das der Innendienst nie
 * sieht — und niemand merkt es, weil beide Seiten für sich stimmig aussehen.
 *
 * Das ist dieselbe Familie wie die Paketpreise: nicht die zweite Kopie ist
 * das Problem, sondern das unbemerkte Auseinanderlaufen.
 */
const fs = require('fs');
const path = require('path');

const QUELLE = path.join(__dirname, '..');

/** Die `key`-Werte aus einem `FREIGABEN`-Block. */
function schluessel(datei) {
  const text = fs.readFileSync(path.join(QUELLE, datei), 'utf8');
  const ab = text.indexOf('FREIGABEN = [');
  expect(ab).toBeGreaterThan(-1);
  const bis = text.indexOf('];', ab);
  return [...text.slice(ab, bis).matchAll(/key:\s*'([^']+)'/g)].map((m) => m[1]);
}

test('Innendienst und Kunde sprechen über dieselben Freigaben', () => {
  // Arrange & Act
  const innendienst = schluessel('components/BriefingTab.jsx');
  const kunde = schluessel('components/kunde/Projektfreigaben.jsx');

  // Assert — Reihenfolge inbegriffen: Sie folgt dem Ablauf, und ein
  // vertauschter Punkt wäre eine andere Aussage über das Projekt.
  expect(kunde).toEqual(innendienst);
});

test('es sind die elf, die den Ablauf tragen', () => {
  const kunde = schluessel('components/kunde/Projektfreigaben.jsx');

  expect(kunde).toHaveLength(11);
  // Die beiden, bei denen der Unterschied zwischen Nachweis und Behauptung
  // zählt — wer sie umbenennt, soll hier vorbeikommen.
  expect(kunde).toContain('abnahme_go_live');
  expect(kunde).toContain('rechtliches');
});
