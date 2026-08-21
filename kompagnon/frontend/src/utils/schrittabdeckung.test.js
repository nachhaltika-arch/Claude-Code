/**
 * Jeder Schritt muss etwas anzeigen können.
 *
 * `KASSidebar.SCHRITTE` nennt je Schritt entweder eine Ansicht (`view`) oder
 * eine Komponente (`component`). Eine Komponente ohne passenden `case` in
 * `ProzessFlow.SchrittInhalt` ist ein Menüpunkt, der auf nichts zeigt: Der
 * Schritt lässt sich anklicken, der Bereich bleibt leer, und nichts meldet
 * einen Fehler.
 *
 * Beim Abbau des Legacy-Editors am 21.08.2026 war das die eigentliche Gefahr:
 * `GeoOptimizer` und `LeistungsseitenWizard` hatten ihren `case` nur in
 * `ProzessFlowV3` — der Datei, die verschwinden sollte.
 *
 * Gelesen wird der Quelltext, nicht das Modul: `ProzessFlow` zieht über seine
 * Nachbarn ein `import.meta` herein, an dem der Testlauf abbricht.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..');

function lies(datei) {
  return fs.readFileSync(path.join(WURZEL, datei), 'utf8');
}

function gebrauchteKomponenten() {
  const quelle = lies('components/KASSidebar.jsx');
  const liste = quelle.match(/const SCHRITT_FOLGE = \[([\s\S]*?)\n\];/);
  expect(liste).not.toBeNull();
  return [...liste[1].matchAll(/component: '([A-Za-z]+)'/g)].map((m) => m[1]);
}

function vorhandeneFaelle() {
  return new Set(
    [...lies('components/ProzessFlow.jsx').matchAll(/case '([A-Za-z]+)':/g)].map((m) => m[1]),
  );
}

test('jede Schritt-Komponente hat einen Zweig in ProzessFlow', () => {
  // Arrange
  const gebraucht = gebrauchteKomponenten();
  const vorhanden = vorhandeneFaelle();

  // Act
  const fehlt = gebraucht.filter((name) => !vorhanden.has(name));

  // Assert
  expect(gebraucht.length).toBeGreaterThan(0);
  expect(fehlt).toEqual([]);
});

test('niemand navigiert mehr auf die Legacy-Route', () => {
  // Gesucht wird die **Adresse im Code**, nicht das Wort. Zwei Fassungen
  // dieses Wächters gaben vorher Fehlalarm: Die erste traf jedes „Legacy" in
  // einem Kommentar, die zweite die Backticks, mit denen ein Kommentar eine
  // Adresse zitiert. Ein Wächter mit Fehlalarmen wird abgeschaltet — deshalb
  // fallen Kommentare hier vor der Suche weg.
  //
  // Warum überhaupt: `/app/projects/:id/legacy` gibt es seit dem 21.08.2026
  // nicht mehr, und der Auffang schickt jeden unbekannten Pfad auf `/login`.
  // Genau diese Kette war L-64 — ein Knopf, der still bei der Anmeldung endet.
  const ohneKommentare = (quelle) => quelle
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:])\/\/.*$/gm, '$1');

  const treffer = [];
  const durchsuche = (ordner) => {
    fs.readdirSync(path.join(WURZEL, ordner), { withFileTypes: true }).forEach((eintrag) => {
      const relativ = path.join(ordner, eintrag.name);
      if (eintrag.isDirectory()) return durchsuche(relativ);
      if (!/\.(js|jsx)$/.test(eintrag.name) || /\.test\./.test(eintrag.name)) return undefined;
      if (/\/legacy\b/.test(ohneKommentare(lies(relativ)))) treffer.push(relativ);
      return undefined;
    });
  };
  durchsuche('.');

  expect(treffer).toEqual([]);
});
