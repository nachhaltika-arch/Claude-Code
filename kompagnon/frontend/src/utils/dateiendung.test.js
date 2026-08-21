/**
 * L-33: Wer JSX schreibt, nennt die Datei `.jsx`.
 *
 * `CustomerDetail.js` trug 2.497 Zeilen JSX unter der Endung für einfaches
 * JavaScript. Beim Nachsehen waren es nicht eine, sondern **sechs** Dateien —
 * die fünf Akademie-Seiten hatten denselben Mangel und standen in keiner
 * Lückenliste.
 *
 * Warum das mehr ist als Ordnung: Werkzeuge unterscheiden nach Endung.
 * Editoren, Linter-Regeln und Suchen nach jsx-Mustern gehen an solchen
 * Dateien vorbei — und in einer davon lagen die 15 namenlosen Formularfelder
 * aus L-17, die deshalb erst spät auffielen.
 */
const fs = require('fs');
const path = require('path');

const WURZEL = path.join(__dirname, '..');

function dateienEinsammeln(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) dateienEinsammeln(voll, treffer);
    else if (eintrag.name.endsWith('.js') && !eintrag.name.includes('.test.')) treffer.push(voll);
  }
  return treffer;
}

test('keine .js-Datei enthält JSX', () => {
  // Nicht jede spitze Klammer ist JSX. `grapesjs/handwerk-blocks.js` erzeugt
  // **HTML als Zeichenkette** für Kundenseiten — `<section style="…">` — und
  // ist zu Recht eine `.js`-Datei. Unterschieden wird deshalb an dem, was nur
  // JSX hat: ein Attribut in geschweiften Klammern (`style={{…}}`) oder ein
  // Element mit grossem Anfangsbuchstaben, also eine Komponente.
  const JSX_ATTRIBUT = /<[a-z][a-zA-Z0-9]*\s+[a-zA-Z-]+=\{/;
  const KOMPONENTE = /<[A-Z][A-Za-z0-9]*[\s/>]/;

  const mitJsx = dateienEinsammeln(WURZEL)
    .filter((datei) => {
      const text = fs.readFileSync(datei, 'utf8')
        .replace(/\{?\/\*[\s\S]*?\*\/\}?/g, '')
        .replace(/^\s*\/\/.*$/gm, '');
      return JSX_ATTRIBUT.test(text) || KOMPONENTE.test(text);
    })
    .map((datei) => path.relative(WURZEL, datei).split(path.sep).join('/'));

  expect(mitJsx).toEqual([]);
});
