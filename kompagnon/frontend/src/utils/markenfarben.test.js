import fs from 'fs';
import path from 'path';

/**
 * Die Markenfarben gehören ins Token-System, nicht in eine Komponente.
 *
 * Befund vom 19.08.2026 (L-32). Sieben Dateien trugen sie als lokale
 * Konstanten:
 *
 *     const KC_DARK   = '#004F59';
 *     const KC_MID    = '#008EAA';
 *     const KC_YELLOW = '#FAE600';
 *
 * Das sah nach Kosmetik aus und war keine. `styles/tokens.css` gibt zweien
 * davon im **Dunkelmodus** andere Werte:
 *
 *     --kc-dark   #004F59  →  #003840
 *     --kc-mid    #008EAA  →  #40c4df
 *
 * Die Komponenten waren damit auf den Hellwerten eingefroren — und `#008EAA`
 * auf dunklem Grund ist genau das Kontrastproblem, für das der Dunkelmodus
 * den Ton absichtlich aufhellt. Dieselbe Fehlerklasse wie die 140 Stellen
 * weißer Schrift vom 18.08.
 *
 * **Geprüft wird die Konstante, nicht jeder Hexwert.** Nachgezählt kommen die
 * drei Farben an 39 Stellen in 21 Dateien vor, und ein Teil davon ist
 * richtig so:
 *
 *   - `utils/tokenwerte.js` löst Token-Ketten zu Werten auf und **muss** sie
 *     kennen
 *   - `grapesjs/handwerk-blocks.js` erzeugt **Kundenseiten** — die haben
 *     unsere CSS-Variablen nicht
 *   - die öffentlichen Marketing-Seiten stehen außerhalb des Tool-Systems
 *
 * Ein Test, der jede Ziffer verbietet, träfe die drei mit. Die Konstante
 * dagegen ist immer falsch: Sie friert einen Modus ein.
 */

const SRC = path.join(__dirname, '..');

// `const IRGENDWAS = '#004F59'` — eine Markenfarbe, festgehalten in einer Datei.
const KONSTANTE = /const\s+\w+\s*=\s*['"]#(?:004F59|008EAA|FAE600)['"]/gi;

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

describe('Markenfarben', () => {
  test('keine Datei friert eine Markenfarbe in einer Konstante ein', () => {
    const schuldige = [];

    for (const datei of dateienSammeln(SRC)) {
      const inhalt = fs.readFileSync(datei, 'utf8');
      const treffer = inhalt.match(KONSTANTE);
      if (treffer) {
        schuldige.push(`${path.relative(SRC, datei)}: ${treffer.join(', ')}`);
      }
    }

    expect(schuldige).toEqual([]);
  });
});
