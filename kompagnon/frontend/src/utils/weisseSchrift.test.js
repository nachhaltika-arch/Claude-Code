/**
 * Weisse Schrift steht nur auf Flächen, auf denen sie in beiden Modi lesbar ist.
 *
 * UX-19a, gefunden beim Umbau der Kundenseiten: Die Anwendung baut Knöpfe als
 * `background: var(--brand-primary)` mit `color: '#fff'`. Im Hellmodus ist das
 * Dark Teal — 9.28, mühelos. Im Dunkelmodus zeigt derselbe Token auf das helle
 * Türkis, und Weiss darauf erreicht **2.06**. Der Knopf sieht dann aus wie
 * eine leere Fläche.
 *
 * Der Fehler ist nicht zu sehen, solange man im Hellmodus arbeitet, und er
 * betrifft nicht eine Stelle, sondern ein Bauprinzip. Deshalb misst dieser
 * Test alle Stellen auf einmal, statt einzelne Bildschirme zu prüfen.
 *
 * Was er NICHT sieht: weisse Schrift auf einer Fläche, die kein Token nennt
 * (fester Hexwert, Verlauf, geerbte Fläche der Eltern). Diese Stellen zählt
 * er und nennt ihre Zahl — damit aus dem Schweigen kein „geprüft" wird.
 */
import fs from 'fs';
import path from 'path';

import { AA_TEXT, kontrast } from './kontrast';
import { tabelle, wert } from './tokenwerte';

const SRC = path.join(__dirname, '..');
const CSS = fs.readFileSync(path.join(SRC, 'styles', 'tokens.css'), 'utf8');
const MODI = { hell: tabelle(CSS, 'hell'), dunkel: tabelle(CSS, 'dunkel') };

const WEISS = /color:\s*['"](#fff|#ffffff|white)['"]/g;

function dateien(verzeichnis = SRC) {
  return fs.readdirSync(verzeichnis, { withFileTypes: true }).flatMap((eintrag) => {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) return dateien(voll);
    if (!/\.jsx?$/.test(eintrag.name) || eintrag.name.includes('.test.')) return [];
    return [voll];
  });
}

/**
 * Der innerste Klammerblock, in dem eine Fundstelle liegt.
 *
 * Nicht auf `style={{` ankern: Farben stehen genauso oft in gewöhnlichen
 * Objekten (`const btnPrimary = { background: …, color: 'white' }`) — in
 * `Courses.jsx` zum Beispiel, und das ist ein echter Knopf. Wer nur
 * `style={{` sucht, übersieht sie; wer den nächsten früheren `style={{}}`
 * nimmt, misst gegen eine fremde Fläche. Beides ist schon passiert.
 */
function rumpfUm(text, stelle) {
  let tiefe = 0;
  let start = -1;
  for (let i = stelle; i >= 0; i -= 1) {
    if (text[i] === '}') tiefe += 1;
    else if (text[i] === '{') {
      if (tiefe === 0) { start = i; break; }
      tiefe -= 1;
    }
  }
  if (start < 0) return null;

  tiefe = 0;
  for (let i = start; i < text.length; i += 1) {
    if (text[i] === '{') tiefe += 1;
    else if (text[i] === '}') {
      tiefe -= 1;
      if (tiefe === 0) return text.slice(start, i);
    }
  }
  return null;
}

function erheben() {
  const treffer = [];
  let ohneToken = 0;

  for (const datei of dateien()) {
    const text = fs.readFileSync(datei, 'utf8');
    const kurz = path.relative(SRC, datei);
    for (const fund of text.matchAll(WEISS)) {
      const rumpf = rumpfUm(text, fund.index);
      // Beides messen: Flächen als Token und Flächen als fester Hexwert.
      // Nur Tokens zu prüfen hiesse, ausgerechnet die unsaubere Hälfte
      // ungeprüft zu lassen.
      const flaechen = rumpf
        ? [...new Set([
            ...[...rumpf.matchAll(/back(?:ground|groundColor):[^,\n]*?var\((--[a-z0-9-]+)\)/g)]
              .map((m) => m[1]),
            ...[...rumpf.matchAll(/back(?:ground|groundColor):[^,\n]*?(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b/g)]
              .map((m) => m[1]),
          ])]
        : [];
      if (flaechen.length === 0) {
        ohneToken += 1;
        continue;
      }
      const zeile = text.slice(0, fund.index).split('\n').length;
      flaechen.forEach((token) => treffer.push({ datei: kurz, zeile, token }));
    }
  }
  return { treffer, ohneToken };
}

const { treffer, ohneToken } = erheben();

describe('Weisse Schrift auf Token-Flächen', () => {
  test('die Erhebung findet überhaupt Stellen', () => {
    expect(treffer.length + ohneToken).toBeGreaterThan(50);
  });

  test('jede Fläche trägt Weiss in beiden Modi lesbar', () => {
    const durchgefallen = treffer.flatMap(({ datei, zeile, token }) =>
      Object.entries(MODI).flatMap(([modus, karte]) => {
        // Ein fester Hexwert ist in beiden Modi derselbe.
        const farbe = token.startsWith('#') ? token : wert(token, karte);
        if (!farbe) return [];
        const gemessen = kontrast('#ffffff', farbe);
        return gemessen >= AA_TEXT
          ? []
          : [`${datei}:${zeile} — Weiss auf ${token} (${modus}): ${gemessen}`];
      }),
    );

    expect(durchgefallen.slice(0, 12)).toEqual([]);
    expect(durchgefallen).toEqual([]);
  });
});
