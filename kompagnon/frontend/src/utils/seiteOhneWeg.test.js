/**
 * Eine Seite, die importiert und nie gerendert wird, ist nicht vorhanden.
 *
 * **Der Befund vom 31.08.2026 (L-105).** `pages/ContactImport.jsx` — der
 * CSV-Import für Kontakte — steht in `App.jsx` im Importblock und wird dort
 * **nirgends gerendert**. Es gibt keine Route und keinen Menüeintrag. Die
 * Seite ist fertig, ihr Backend auch (`POST /api/leads/import/csv` und
 * `/import/manual`), und niemand kommt hin.
 *
 * **Zwei vorhandene Werkzeuge sehen das nicht, und beide aus gutem Grund:**
 *
 * * `tools/unerreichbare-dateien.py` zählt **Import-Anweisungen**. Die Datei
 *   *wird* importiert — von `App.jsx` — also gilt sie als erreicht.
 * * `tools/unaufgerufene-routen.py` fragt, ob eine Adresse in einer
 *   Frontend-Datei **vorkommt**. Sie kommt vor. Die beiden Import-Routen
 *   zählen deshalb als angeschlossen, obwohl sie es nicht sind.
 *
 * Zusammen ergeben sie eine Lücke, die genau so aussieht wie Ordnung: Datei
 * erreicht, Endpunkte gerufen, kein Befund. **Der Bau meldet es sogar** —
 * „'ContactImport' is defined but never used" — aber unter 53 anderen
 * Warnungen, und die CI baut mit `CI: false`, weil sonst jede davon rot wäre.
 *
 * Deshalb dieser Test: Er stellt genau die eine Frage, die keines der beiden
 * anderen stellt — **wird diese Seite je gerendert?**
 */
import fs from 'fs';
import path from 'path';

const APP = path.join(__dirname, '..', 'App.jsx');

/**
 * Seiten, die bewusst importiert und nicht gerendert werden — je mit Grund.
 *
 * `ContactImport` steht hier, weil „Route bauen oder Seite entfernen" eine
 * Produktfrage ist und keine Aufräumfrage: Wollen wir den Kontakt-CSV-Import
 * überhaupt? Dieselbe Entscheidung, die David am 24.08. für `SalesPipeline`,
 * `TemplateGallery` und `QAChecklist` einzeln getroffen hat (L-95).
 *
 * **Die Ausnahme ist kein Freibrief, sondern ein Merkzettel.** Der Test unten
 * rechnet nach, dass sie noch gilt.
 */
const AUSNAHMEN = {
  ContactImport:
    'CSV-Import für Kontakte. Fertig gebaut, Backend vorhanden, ohne Route '
    + 'und ohne Menüeintrag. Anschließen oder entfernen ist Davids '
    + 'Entscheidung (L-105, 31.08.2026).',
};

const quelle = fs.readFileSync(APP, 'utf8');

/** Die Seitenkomponenten, die `App.jsx` importiert. */
function importierteSeiten() {
  return [...quelle.matchAll(/^import (\w+) from '\.\/pages\/[\w/]+';/gm)]
    .map(m => m[1]);
}

function wirdGerendert(name) {
  return new RegExp(`<${name}\\b`).test(quelle);
}

describe('Jede eingebundene Seite hat einen Weg', () => {
  const seiten = importierteSeiten();

  test('es werden überhaupt Seiten gefunden', () => {
    // Die positive Zusicherung neben der Abwesenheit. Ohne sie wäre der Test
    // unten auch dann grün, wenn der Ausdruck nichts mehr trifft — und genau
    // so war der Kontrast-Wächter am 30.08. grün.
    expect(seiten.length).toBeGreaterThan(30);
  });

  test('keine Seite wird importiert, ohne je gerendert zu werden', () => {
    const ohneWeg = seiten
      .filter(n => !wirdGerendert(n))
      .filter(n => !(n in AUSNAHMEN));

    expect(ohneWeg).toEqual([]);
  });

  test('die Ausnahmen gelten noch — sonst sind sie ein Loch', () => {
    const veraltet = [];
    for (const name of Object.keys(AUSNAHMEN)) {
      if (!seiten.includes(name)) {
        veraltet.push(`${name}: wird gar nicht mehr importiert`);
      } else if (wirdGerendert(name)) {
        veraltet.push(`${name}: hat jetzt einen Weg — Ausnahme streichen`);
      }
    }
    expect(veraltet).toEqual([]);
  });
});
