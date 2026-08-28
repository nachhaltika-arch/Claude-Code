/**
 * Jede Farbe, die als Text benutzt wird, muss auf ihrem Grund lesbar sein (L-17).
 *
 * **Der Unterschied zu `tokenKontrast.test.js`.** Der prüft, ob die *als
 * Kommentar notierten* Kontrastzahlen stimmen. Tokens ohne Kommentar prüft er
 * nicht — und genau dort lag der Fehler.
 *
 * **Der Fund vom 28.08.2026.** `--brand-primary-mid` stand im dunklen
 * Tokensatz auf `#2a5a6a`. Als **Textfarbe** auf `--surface` sind das **2.18**;
 * die Schwelle für normalen Text ist 4.5. Das Token wird an **78 Stellen** als
 * `color:` gesetzt — im Dunkelmodus war dieser Text unlesbar, und niemandem
 * war es aufgefallen, weil keine Zahl danebenstand. Jetzt `#3f9fb2` (5.37).
 *
 * **Drei eigene Fehlmessungen beim Bauen dieses Tests, alle in dieselbe
 * Richtung — und deshalb steht die Lehre hier und nicht nur im Verlauf:**
 *
 * 1. Erst wurde *jedes* Text-Token gegen *jede* Fläche gerechnet. Das meldete
 *    zwölf Verstöße, von denen keiner einer war: `--text-inverse` und
 *    `--text-on-brand` gehören nicht auf `--surface`, sie sind für dunklen
 *    beziehungsweise markenfarbenen Grund gemacht.
 * 2. Dann wurde `--text-on-brand` gegen `--brand-primary-mid` gerechnet — auch
 *    falsch: Dieses Token ist keine Fläche, es ist eine Schriftfarbe.
 * 3. `--brand-primary-light` fiel mit 1.43 durch und wird **nirgends** als
 *    Text benutzt (0 Vorkommen, 35 als Hintergrund).
 *
 * Ein Kontrasttest, der Paare prüft, die es nicht gibt, ist ein
 * Fehlalarm-Erzeuger — und wird abgeschaltet. Deshalb steht hier eine
 * **ausdrückliche Paarliste** statt eines Kreuzprodukts.
 *
 * **Und deshalb prüft der letzte Test die Ausnahmen nach.** Eine Ausnahmeliste,
 * die niemand nachrechnet, verwandelt sich in ein Loch: Sobald jemand
 * `--brand-primary-light` doch als Schriftfarbe verwendet, gilt hier weiter
 * „wird nicht als Text benutzt" — und die Prüfung schweigt zu genau dem Fall,
 * für den sie gebaut wurde.
 */
import fs from 'fs';
import path from 'path';

import { AA_TEXT, kontrast } from './kontrast';

const WURZEL = path.join(__dirname, '..');
const TOKENS = path.join(WURZEL, 'styles', 'tokens.css');

/** Welche Schriftfarbe ist für welchen Grund gemacht. */
const PAARE = [
  ['--text', '--surface'],
  ['--text', '--paper'],
  ['--text', '--bg-active'],
  ['--text-60', '--surface'],
  ['--text-60', '--paper'],
  ['--text-60', '--bg-active'],
  ['--text-45', '--surface'],
  ['--text-45', '--paper'],
  ['--brand-primary-mid', '--surface'],
  ['--brand-primary-mid', '--paper'],
];

/**
 * Absichtlich nicht geprüft — mit Grund, und der Grund wird nachgerechnet.
 * `pruefeUngenutzt` heisst: Das Token darf im Quellbaum nicht als `color:`
 * auftauchen; tut es das doch, ist die Ausnahme hinfällig.
 */
const AUSNAHMEN = [
  { token: '--text-30', pruefeUngenutzt: false,
    grund: 'Absichtlich schwach — abgeschaltete Bedienelemente, von WCAG 1.4.3 ausgenommen.' },
  { token: '--text-placeholder', pruefeUngenutzt: false,
    grund: 'Platzhalter, kein Inhalt. Der Feldname steht seit dem 21.08. programmatisch daneben.' },
  { token: '--brand-primary-light', pruefeUngenutzt: true,
    grund: 'Ist eine Fläche, keine Schriftfarbe — 35 Vorkommen als Hintergrund, null als Text.' },
  { token: '--brand-primary-deeper', pruefeUngenutzt: true,
    grund: 'Ebenfalls Fläche; als Text käme sie auf 3.97 und wäre ein Befund.' },
];

/** Zeilennummern der Blockanfänge — wie in `tokenKontrast.test.js`. */
function bloecke(zeilen) {
  const anfaenge = [];
  zeilen.forEach((zeile, i) => {
    if (/^(:root|@media|\[data-theme)/.test(zeile)) anfaenge.push({ i, kopf: zeile.trim() });
  });
  return anfaenge.map((a, n) => ({
    kopf: a.kopf,
    von: a.i,
    bis: (anfaenge[n + 1] || { i: zeilen.length }).i,
  }));
}

function werteIm(zeilen, block) {
  const werte = {};
  for (let i = block.von; i < block.bis; i += 1) {
    const treffer = zeilen[i].match(/^\s*(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})\s*;/);
    if (treffer) werte[treffer[1]] = treffer[2];
  }
  return werte;
}

const zeilen = fs.readFileSync(TOKENS, 'utf8').split('\n');
const alleBloecke = bloecke(zeilen);

describe('Kontrast der gepaarten Tokens', () => {
  test.each(alleBloecke.map(b => [b.kopf, b]))('%s', (_kopf, block) => {
    const werte = werteIm(zeilen, block);
    const durchgefallen = [];

    PAARE.forEach(([schrift, grund]) => {
      // Nicht jeder Block definiert jedes Token neu — was hier fehlt, erbt.
      if (!werte[schrift] || !werte[grund]) return;
      const wert = kontrast(werte[schrift], werte[grund]);
      if (wert < AA_TEXT) {
        durchgefallen.push(`${schrift} auf ${grund}: ${wert.toFixed(2)} < ${AA_TEXT}`);
      }
    });

    expect(durchgefallen).toEqual([]);
  });

  test('mindestens ein Block prüft wirklich Paare', () => {
    // Ohne das wäre der Test oben auch dann grün, wenn die Namen nicht mehr
    // passen und jedes Paar übersprungen wird.
    const geprueft = alleBloecke.map(b => {
      const w = werteIm(zeilen, b);
      return PAARE.filter(([s, g]) => w[s] && w[g]).length;
    });
    expect(Math.max(...geprueft)).toBeGreaterThanOrEqual(PAARE.length - 2);
  });
});

describe('Die Ausnahmen halten noch', () => {
  const quellen = [];
  (function sammle(ordner) {
    fs.readdirSync(ordner, { withFileTypes: true }).forEach(eintrag => {
      const voll = path.join(ordner, eintrag.name);
      if (eintrag.isDirectory()) {
        if (eintrag.name !== 'node_modules') sammle(voll);
      } else if (/\.(js|jsx|css)$/.test(eintrag.name) && !/\.test\./.test(eintrag.name)) {
        quellen.push(voll);
      }
    });
  })(WURZEL);

  test.each(AUSNAHMEN.filter(a => a.pruefeUngenutzt).map(a => [a.token, a]))(
    '%s wird nicht als Schriftfarbe benutzt', (token, ausnahme) => {
      const muster = new RegExp(`color:\\s*['"\`]?\\s*var\\(\\s*${token}\\b`);
      const fundstellen = quellen
        .filter(datei => muster.test(fs.readFileSync(datei, 'utf8')))
        .map(datei => path.relative(WURZEL, datei));

      expect({ token, grund: ausnahme.grund, fundstellen }).toEqual({
        token, grund: ausnahme.grund, fundstellen: [],
      });
    });

  test('jede Ausnahme trägt einen Grund', () => {
    AUSNAHMEN.forEach(a => expect(a.grund.length).toBeGreaterThan(30));
  });
});
