import fs from 'fs';
import path from 'path';

import { AA_TEXT, alsRgb, kontrast } from './kontrast';

describe('kontrast', () => {
  test('Schwarz auf Weiß ist der Höchstwert', () => {
    expect(kontrast('#000000', '#FFFFFF')).toBe(21);
  });

  test('eine Farbe gegen sich selbst ist 1', () => {
    expect(kontrast('#9AACAE', '#9AACAE')).toBe(1);
  });

  test('die Reihenfolge ist egal', () => {
    expect(kontrast('#647071', '#FAFAFA')).toBe(kontrast('#FAFAFA', '#647071'));
  });

  test('die Kurzform ist dieselbe Farbe', () => {
    expect(alsRgb('#ccc')).toEqual(alsRgb('#cccccc'));
  });

  test('das Doppelkreuz darf fehlen', () => {
    expect(alsRgb('9AACAE')).toEqual([154, 172, 174]);
  });

  test('was keine Farbe ist, wird abgewiesen', () => {
    expect(() => kontrast('rot', '#FFFFFF')).toThrow();
  });
});

// ── Die Palette selbst ────────────────────────────────────────────────
//
// Befund vom 17.08.2026: `--text-30` diente app-weit als Farbe für
// Beschriftungen — 911 Verwendungen über `--text-tertiary`. Auf der App-Fläche
// erreichte sie **2.13**. Die Schwelle für Text ist 4.5. Deshalb las sich die
// Kachelreihe des Dashboards wie Dekoration: Nicht die Zahlen waren zu
// schwach (8.89), sondern die Wörter darunter, die sagen, was die Zahl ist.
//
// Dieser Test liest die echte Datei. Wer einen Ton aufhellt, bricht ihn.

const TOKENS = fs.readFileSync(
  path.join(__dirname, '..', 'styles', 'tokens.css'), 'utf8',
);

/** Liest `--name: #wert;` aus einem Abschnitt der Datei. */
function ton(name, abschnitt) {
  const treffer = abschnitt.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`));
  if (!treffer) throw new Error(`${name} steht nicht in diesem Abschnitt`);
  return treffer[1];
}

const hell = TOKENS.slice(0, TOKENS.indexOf('@media (prefers-color-scheme: dark)'));
const dunkel = TOKENS.slice(TOKENS.indexOf('[data-theme="dark"]'));

describe('Textfarben der Palette', () => {
  // Beide Flächen, auf denen Text steht. `surface` ist die dunklere von
  // beiden und damit der Maßstab — dort wird es zuerst eng.
  const flaechenHell = ['paper', 'surface'];

  test.each(flaechenHell)('--text-45 besteht auf %s', (flaeche) => {
    expect(kontrast(ton('text-45', hell), ton(flaeche, hell)))
      .toBeGreaterThanOrEqual(AA_TEXT);
  });

  test.each(flaechenHell)('--text-60 besteht auf %s', (flaeche) => {
    expect(kontrast(ton('text-60', hell), ton(flaeche, hell)))
      .toBeGreaterThanOrEqual(AA_TEXT);
  });

  test.each(flaechenHell)('--text besteht auf %s', (flaeche) => {
    expect(kontrast(ton('text', hell), ton(flaeche, hell)))
      .toBeGreaterThanOrEqual(AA_TEXT);
  });

  test.each(['paper', 'surface'])('im Dunkelmodus besteht --text-45 auf %s', (flaeche) => {
    expect(kontrast(ton('text-45', dunkel), ton(flaeche, dunkel)))
      .toBeGreaterThanOrEqual(AA_TEXT);
  });

  test('der Knopf auf hervorgehobener Fläche ist lesbar', () => {
    // UX-18: „Vollständigen Bericht anzeigen" stand mit `--brand-primary-mid`
    // auf `--bg-active` — 3.39 im Hellmodus, also unter der Schwelle. Er sah
    // deaktiviert aus, war es aber nie. Jetzt `--brand-primary` (= kc-dark).
    expect(kontrast(ton('kc-dark', hell), ton('bg-active', hell)))
      .toBeGreaterThanOrEqual(AA_TEXT);
    expect(kontrast(ton('kc-mid', dunkel), ton('bg-active', dunkel)))
      .toBeGreaterThanOrEqual(AA_TEXT);
  });

  test('die Schrift auf dem Markenknopf ist in beiden Modi lesbar', () => {
    // Gefunden beim Umbau der Kundenseiten (UX-19): Die Anwendung setzt
    // Knöpfe seit jeher als `--brand-primary` mit weisser Schrift. Im
    // Hellmodus ist das Dark Teal — 9.28, mühelos. Im Dunkelmodus zeigt
    // `--brand-primary` auf das helle Türkis, und Weiss darauf erreicht
    // **2.06**. Auf dem Anmeldeknopf des Kundenportals wäre das die erste
    // Fläche nach dem Kauf gewesen.
    //
    // `--text-on-brand` dreht die Tinte im Dunkelmodus, statt die
    // Markenfarbe zu ändern.
    expect(kontrast(ton('text-on-brand', hell), ton('kc-dark', hell)))
      .toBeGreaterThanOrEqual(AA_TEXT);
    expect(kontrast(ton('text-on-brand', dunkel), ton('kc-mid', dunkel)))
      .toBeGreaterThanOrEqual(AA_TEXT);
  });

  // ── Statustöne ──────────────────────────────────────────────────
  //
  // Am 18.08.2026 nachgemessen, weil beim Umbau der weissen Schrift auffiel,
  // dass die Statusfarben nie gegen ihre eigenen Flächen geprüft worden
  // waren. Im Hellmodus lagen drei von vier unter der Schwelle: success
  // 4.11, warn 4.08 und info 3.48 — und im Block [data-theme="light"] stand
  // warn auf #B8860B mit **2.94**. Im Dunkelmodus bestand alles, weshalb es
  // niemandem auffällt, der dunkel arbeitet.
  describe.each(['success', 'warn', 'error', 'info'])('--%s', (art) => {
    test.each(['surface', 'paper'])('besteht auf --%s in beiden Modi', (flaeche) => {
      [hell, dunkel].forEach((abschnitt) => {
        expect(kontrast(ton(art, abschnitt), ton(flaeche, abschnitt)))
          .toBeGreaterThanOrEqual(AA_TEXT);
      });
    });

    test('besteht auf der eigenen Fläche in beiden Modi', () => {
      [hell, dunkel].forEach((abschnitt) => {
        expect(kontrast(ton(art, abschnitt), ton(`${art}-bg`, abschnitt)))
          .toBeGreaterThanOrEqual(AA_TEXT);
      });
    });
  });

  test('--text-30 bleibt bewusst hell und ist deshalb kein Textton', () => {
    // Der Ton hat seine Berechtigung für Trennlinien und Zierrat. Der Test
    // hält nur fest, dass er die Textschwelle NICHT erreicht — wer ihn für
    // Text einsetzt, tut es also nicht aus Versehen.
    expect(kontrast(ton('text-30', hell), ton('surface', hell)))
      .toBeLessThan(AA_TEXT);
  });
});
