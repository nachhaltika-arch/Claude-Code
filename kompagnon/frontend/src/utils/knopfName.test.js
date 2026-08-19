import fs from 'fs';
import path from 'path';

/**
 * Ein Knopf, der nur ein Zeichen zeigt, braucht einen Namen.
 *
 * Befund vom 19.08.2026 (L-17). Zwölf Schaltflächen bestanden nur aus einem
 * Symbol — zehnmal `×` oder `✕` zum Schließen, einmal `✓` zum Speichern. Ohne
 * `aria-label` liest ein Screenreader daraus „mal" oder gar nichts, und wer
 * die Anwendung mit der Tastatur bedient, weiß nicht, worauf er steht.
 *
 * Das ist WCAG 4.1.2 (Name, Rolle, Wert) und damit **genau das, was wir bei
 * Kunden prüfen**. Ein Werkzeug, das BFSG-Konformität verkauft und selbst
 * namenlose Knöpfe hat, ist schwer zu verteidigen.
 *
 * Der Test prüft die Regel, nicht die zwölf Stellen: Der nächste Dialog
 * bekommt sonst wieder ein nacktes `×`.
 *
 * **Nicht geprüft** wird der Rest der Barrierefreiheit. 20 von 182 Dateien
 * führen überhaupt ARIA — das bleibt offen und steht so in der Lückenliste.
 * Diese Datei schließt eine Klasse, nicht das Thema.
 */

const SRC = path.join(__dirname, '..');

// Ein Knopf, dessen ganzer Inhalt aus höchstens vier Zeichen besteht und
// keinen Buchstaben und keine Ziffer enthält — also ein reines Symbol.
const SYMBOLKNOPF = /<button(?![^>]*(?:aria-label|title=))[^>]*>\s*([^<]{1,4})\s*<\/button>/g;

function dateienSammeln(ordner, treffer = []) {
  for (const eintrag of fs.readdirSync(ordner, { withFileTypes: true })) {
    const voll = path.join(ordner, eintrag.name);
    if (eintrag.isDirectory()) {
      if (eintrag.name === 'node_modules') continue;
      dateienSammeln(voll, treffer);
    } else if (/\.(js|jsx)$/.test(eintrag.name) && !/\.test\.js$/.test(eintrag.name)) {
      treffer.push(voll);
    }
  }
  return treffer;
}

describe('Namen von Symbolknöpfen', () => {
  test('kein Knopf zeigt nur ein Zeichen ohne aria-label', () => {
    const namenlos = [];

    for (const datei of dateienSammeln(SRC)) {
      const inhalt = fs.readFileSync(datei, 'utf8');
      for (const treffer of inhalt.matchAll(SYMBOLKNOPF)) {
        const inhaltDesKnopfs = treffer[1].trim();
        // Buchstaben oder Ziffern sind selbst schon ein Name („PDF", „OK").
        if (/[\p{L}\p{N}]/u.test(inhaltDesKnopfs)) continue;
        namenlos.push(`${path.relative(SRC, datei)}: „${inhaltDesKnopfs}"`);
      }
    }

    expect(namenlos).toEqual([]);
  });
});
