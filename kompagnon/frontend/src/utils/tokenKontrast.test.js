/**
 * Die Kontrastzahlen in `tokens.css` müssen stimmen.
 *
 * **Warum das ein eigener Test ist (23.08.2026, L-17).** Einige Farbtokens
 * tragen ihren Kontrast als Kommentar neben sich:
 *
 *     --text:    #000000;  // 20.4 auf --surface
 *     --text-60: #4A5A5C;  //  6.5 auf --surface
 *
 * Solche Zahlen sind wertvoll — sie ersparen beim Lesen das Nachrechnen und
 * halten fest, warum eine Farbe so und nicht anders gewählt wurde. Genau
 * deshalb müssen sie stimmen: Eine Zahl, die danebensteht und falsch ist, ist
 * schlimmer als keine, weil ihr niemand misstraut.
 *
 * Beim Nachrechnen war eine falsch. `--text` stand mit **20.4 auf --surface**
 * da; gerechnet sind es **18.96**. Die 20.4 passen zu keinem der beiden
 * Hintergründe genau (`--paper` gibt 20.12) — sie stammen aus einer früheren
 * Fassung der Tokens und sind beim Umfärben nicht mitgewandert. Bestanden hat
 * die Farbe immer, nur die Zahl war Fiktion.
 *
 * Ein zweiter Grund für diesen Test: Beim ersten Nachrechnen kam für
 * `--text-45` **2.21** statt der behaupteten 6.76 heraus, und das sah nach
 * einem groben Ausfall aus. Es war ein Fehler in der Messung — der Kommentar
 * sagt „dunkel", und der dunkle Tokensatz war falsch abgegrenzt worden, weil
 * hinter `@media (prefers-color-scheme: dark)` noch ein
 * `[data-theme="light"]`-Block folgt, der die Werte zurücksetzt. Deshalb
 * grenzt dieser Test die Blöcke ausdrücklich ab, statt am Dateiende zu raten.
 */
import fs from 'fs';
import path from 'path';

import { kontrast } from './kontrast';

const TOKENS = path.join(__dirname, '..', 'styles', 'tokens.css');

/** Zeilennummern der Blockanfänge — `:root`, `@media`, `[data-theme=…]`. */
function bloecke(zeilen) {
  const gefunden = [];
  zeilen.forEach((zeile, i) => {
    if (/^(:root|@media|\[data-theme)/.test(zeile)) gefunden.push(i);
  });
  return gefunden;
}

/** Alle `--name: #hex;` eines Zeilenbereichs. */
function tokensAus(zeilen, von, bis) {
  const gefunden = {};
  for (const zeile of zeilen.slice(von, bis)) {
    const treffer = zeile.match(/(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{3,6})\s*;/);
    if (treffer) gefunden[treffer[1]] = treffer[2];
  }
  return gefunden;
}

function saetze() {
  const zeilen = fs.readFileSync(TOKENS, 'utf8').split('\n');
  const grenzen = bloecke(zeilen);

  const beginnt = (muster) =>
    grenzen.find((i) => muster.test(zeilen[i]));

  const hellVon = grenzen[0];
  const hellBis = grenzen[1] ?? zeilen.length;
  const dunkelVon = beginnt(/^\[data-theme="dark"\]/);
  const dunkelBis = beginnt(/^\[data-theme="light"\]/) ?? zeilen.length;

  const hell = tokensAus(zeilen, hellVon, hellBis);
  return {
    zeilen,
    hell,
    // Der dunkle Satz erbt alles, was er nicht selbst überschreibt.
    dunkel: { ...hell, ...tokensAus(zeilen, dunkelVon, dunkelBis) },
  };
}

/** Jede Zeile mit einer Kontrastbehauptung im Kommentar. */
function behauptungen(zeilen) {
  const heraus = [];
  zeilen.forEach((zeile, i) => {
    const treffer = zeile.match(
      /(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{3,6});\s*\/\*\s*(dunkel:\s*)?([\d.]+)\s+auf\s+(--[a-z0-9-]+)/
    );
    if (treffer) {
      heraus.push({
        zeile: i + 1,
        token: treffer[1],
        farbe: treffer[2],
        istDunkel: Boolean(treffer[3]),
        behauptet: parseFloat(treffer[4]),
        gegen: treffer[5],
      });
    }
  });
  return heraus;
}

describe('Kontrastzahlen in tokens.css', () => {
  const { zeilen, hell, dunkel } = saetze();
  const alle = behauptungen(zeilen);

  test('die Erhebung findet überhaupt Behauptungen', () => {
    // Ohne diese Probe wäre ein leerer Treffersatz ein grüner Test — die
    // Sorte Prüfung, die bestanden aussieht und nichts prüft.
    expect(alle.length).toBeGreaterThan(0);
  });

  test('beide Tokensätze sind sauber abgegrenzt', () => {
    // Der Fehler, der diesen Test veranlasst hat: Hinter dem Dunkelblock
    // folgt ein Hellblock, und wer bis zum Dateiende liest, bekommt Hell.
    expect(hell['--surface']).toBeTruthy();
    expect(dunkel['--surface']).toBeTruthy();
    expect(dunkel['--surface']).not.toBe(hell['--surface']);
  });

  test.each(alle.map((b) => [
    `Zeile ${b.zeile}: ${b.token} = ${b.behauptet} auf ${b.gegen}${b.istDunkel ? ' (dunkel)' : ''}`,
    b,
  ]))('%s', (_name, b) => {
    const satz = b.istDunkel ? dunkel : hell;
    const hintergrund = satz[b.gegen];

    expect(hintergrund).toBeTruthy();

    const gerechnet = kontrast(b.farbe, hintergrund);
    // Eine Nachkommastelle Spielraum: Die Kommentare runden unterschiedlich.
    expect(Math.abs(gerechnet - b.behauptet)).toBeLessThan(0.1);
  });
});
