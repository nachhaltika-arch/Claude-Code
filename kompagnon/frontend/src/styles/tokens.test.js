/**
 * Der helle Modus muss alles zurücknehmen, was der dunkle setzt.
 *
 * Gefunden beim Umbau der Kundenseiten (UX-19), gemessen im Browser:
 * Auf einem Rechner, dessen System auf dunkel steht, ergab die Wahl „hell"
 *
 *     --bg-app       #f0f4f5   (hell, richtig)
 *     --brand-primary #008eaa  (aus dem Dunkelblock, falsch)
 *
 * Grund: `ThemeContext` setzt immer ein `data-theme`, aber der Block
 * `[data-theme="light"]` nennt nur die Flächen- und Textfarben. Alles
 * andere — die Markenaliasse voran — bleibt auf den Werten stehen, die
 * `@media (prefers-color-scheme: dark)` gesetzt hat. Das Ergebnis ist keine
 * der beiden Welten, sondern eine dritte: helle Flächen mit den
 * Markenfarben des Dunkelmodus. Weiß auf `#008eaa` erreicht 3.85 statt der
 * geforderten 4.5 — auf dem Anmeldeknopf des Kundenportals.
 *
 * Die Regel ist deshalb mengenmäßig, nicht ästhetisch: Was der Dunkelblock
 * überschreibt, muss der Hellblock zurückholen.
 */
import fs from 'fs';
import path from 'path';

const TOKENS = fs.readFileSync(path.join(__dirname, 'tokens.css'), 'utf8');

/** Alle `--name:` eines Abschnitts. */
function namen(abschnitt) {
  const treffer = abschnitt.match(/--[a-z0-9-]+\s*:/g) || [];
  return new Set(treffer.map((t) => t.replace(/\s*:$/, '')));
}

function abschnitt(von, bis) {
  const start = TOKENS.indexOf(von);
  if (start < 0) throw new Error(`${von} steht nicht in tokens.css`);
  const ende = bis ? TOKENS.indexOf(bis, start) : TOKENS.length;
  return TOKENS.slice(start, ende < 0 ? TOKENS.length : ende);
}

const DUNKEL_SYSTEM = abschnitt('@media (prefers-color-scheme: dark)', '[data-theme="dark"]');
const DUNKEL_MANUELL = abschnitt('[data-theme="dark"]', '[data-theme="light"]');
const HELL_MANUELL = abschnitt('[data-theme="light"]', '/* ── Skeleton');

describe('Die beiden Modi decken einander', () => {
  test('der Hellblock nimmt jeden Ton des Dunkelblocks zurück', () => {
    const fehlend = [...namen(DUNKEL_SYSTEM)].filter((n) => !namen(HELL_MANUELL).has(n));

    expect(fehlend).toEqual([]);
  });

  test('beide Dunkelblöcke setzen dasselbe', () => {
    // Sonst unterscheidet sich „dunkel gewählt" von „dunkel geerbt".
    const nurSystem = [...namen(DUNKEL_SYSTEM)].filter((n) => !namen(DUNKEL_MANUELL).has(n));
    const nurManuell = [...namen(DUNKEL_MANUELL)].filter((n) => !namen(DUNKEL_SYSTEM).has(n));

    expect({ nurSystem, nurManuell }).toEqual({ nurSystem: [], nurManuell: [] });
  });
});
