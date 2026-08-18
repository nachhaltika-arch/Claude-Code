// Was ein Token in einem Modus wirklich ist.
//
// Warum es das gibt: `--brand-primary` ist kein Wert, sondern ein Verweis —
// im Hellmodus auf `--kc-dark` (#004F59), im Dunkelmodus auf `--kc-mid`
// (#40c4df). Wer eine Farbkombination beurteilen will, muss die Kette
// aufloesen, und zwar je Modus getrennt. Von Hand nachgeschlagen wird das
// falsch: Genau daran lag UX-19a — weisse Schrift auf `--brand-primary` sah
// im Hellmodus mit 9.28 muehelos aus und erreichte im Dunkelmodus 2.06.

/** Grenzen der drei Bloecke in tokens.css. */
const BLOECKE = {
  wurzel: [':root {', '@media (prefers-color-scheme: dark)'],
  dunkel: ['[data-theme="dark"]', '[data-theme="light"]'],
  hell:   ['[data-theme="light"]', '/* ── Skeleton'],
};

function ausschnitt(css, [von, bis]) {
  const start = css.indexOf(von);
  if (start < 0) throw new Error(`${von} steht nicht in tokens.css`);
  const ende = css.indexOf(bis, start);
  return css.slice(start, ende < 0 ? css.length : ende);
}

function paare(abschnitt) {
  const karte = new Map();
  const muster = /(--[a-z0-9-]+)\s*:\s*([^;]+);/g;
  let treffer;
  while ((treffer = muster.exec(abschnitt)) !== null) {
    karte.set(treffer[1], treffer[2].trim());
  }
  return karte;
}

/**
 * Baut die Nachschlagetabelle eines Modus: Wurzel zuerst, dann der
 * modusspezifische Block darueber.
 */
export function tabelle(css, modus) {
  if (modus !== 'hell' && modus !== 'dunkel') {
    throw new Error(`Unbekannter Modus: ${modus}`);
  }
  const karte = new Map(paare(ausschnitt(css, BLOECKE.wurzel)));
  for (const [name, wert] of paare(ausschnitt(css, BLOECKE[modus]))) {
    karte.set(name, wert);
  }
  return karte;
}

/** Loest `var(--a)` → `var(--b)` → `#rrggbb` auf. `null`, wenn kein Farbwert. */
export function wert(name, karte, tiefe = 0) {
  const roh = karte.get(name);
  if (roh === undefined || tiefe > 8) return null;
  const verweis = roh.match(/^var\(\s*(--[a-z0-9-]+)\s*\)$/);
  if (verweis) return wert(verweis[1], karte, tiefe + 1);
  return /^#[0-9a-fA-F]{3,8}$/.test(roh) ? roh : null;
}
