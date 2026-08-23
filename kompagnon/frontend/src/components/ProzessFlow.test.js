/**
 * Von `ProzessFlow.jsx` wird nur `SchrittInhalt` gebraucht (L-25).
 *
 * **Der Befund, 22.08.2026.** Die Datei hatte 2.307 Zeilen und vier Exporte:
 * `PHASEN`, `ALLE_SCHRITTE`, die Standardkomponente `ProzessFlow` — und
 * `SchrittInhalt`. Importiert wird an **einer** Stelle im ganzen Baum, und
 * zwar nur der letzte: `OnlineFertigEditor.jsx:35`.
 *
 * `PHASEN` steht zwar auch in `CustomerPortal.jsx` — aber dort **eigens
 * definiert**, nicht von hier geholt.
 *
 * **Ein Irrtum unterwegs, der teuer geworden waere.** Zuerst sah es so aus,
 * als sei die ganze Datei tot: Keine Seite bindet `ProzessFlow` ein. Das
 * stimmt — aber es wird der **benannte** Export gebraucht, nicht der
 * Standard. Wer nur nach `import ProzessFlow` sucht, findet nichts und
 * loescht 2.307 Zeilen, von denen 1.786 gebraucht werden.
 *
 * Gelesen wird der Quelltext, nicht das Modul: Die Datei zieht ueber ihre
 * Nachbarn ein `import.meta` herein, an dem der Testlauf abbricht — dasselbe
 * Vorgehen wie in `utils/schrittabdeckung.test.js`.
 */
import fs from 'fs';
import path from 'path';

const DATEI = path.join(__dirname, 'ProzessFlow.jsx');
const quelle = () => fs.readFileSync(DATEI, 'utf8');

test('exportiert nur noch, was auch gebraucht wird', () => {
  const text = quelle();

  // **Beide Schreibweisen.** Am Dateiende stand ein Sammelblock
  // `export { … }` mit elf Namen — die erste Fassung dieses Tests suchte nur
  // `export function` und sah ihn nicht. Ein Waechter, der die halbe Datei
  // prueft, meldet Ruhe, wo keine ist.
  const einzeln = [...text.matchAll(/^export\s+(?:default\s+)?(?:function|const)\s+(\w+)/gm)]
    .map((m) => m[1]);
  const sammel = [...text.matchAll(/^export\s*\{([^}]*)\}/gm)]
    .flatMap((m) => m[1].split(',').map((s) => s.trim().split(/\s+as\s+/).pop()))
    .filter(Boolean);

  expect([...einzeln, ...sammel].sort()).toEqual(['SchrittInhalt']);
});

test('die tote Prozessansicht ist weg', () => {
  // `PHASEN` und `ALLE_SCHRITTE` beschrieben die Schrittfolge ein zweites
  // Mal — die gueltige steht in `KASSidebar.SCHRITT_FOLGE`. Zwei Fassungen
  // derselben Liste laufen auseinander; genau das ist bei `_serialize` in
  // den Briefing-Routern passiert (L-27).
  const text = quelle();

  expect(text).not.toMatch(/^const PHASEN = \[/m);
  expect(text).not.toMatch(/^export const ALLE_SCHRITTE/m);
  expect(text).not.toMatch(/^export default function ProzessFlow/m);
});

test('SchrittInhalt selbst ist noch da', () => {
  expect(quelle()).toMatch(/^export function SchrittInhalt/m);
});
