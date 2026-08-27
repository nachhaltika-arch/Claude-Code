import fs from 'fs';
import path from 'path';

/**
 * Ein Link, der nur ein Zeichen zeigt, braucht einen Namen.
 *
 * Dritte Klasse aus L-17, geschlossen am 24.08.2026. Nach den Schaltflächen
 * (19.08.) und den Formularfeldern (21.08.) blieben drei Links übrig, die aus
 * einem einzigen Symbol bestanden: `↗` zur Website des Betriebs, `✉️` für den
 * Zugangslink per Mail, `👁` zur Seitenvorschau. Ein Screenreader liest daraus
 * nichts Brauchbares.
 *
 * Das ist WCAG 2.4.4 (Zweck eines Links) und 4.1.2 — und `link-name` ist
 * eines der Kriterien, die **unser eigenes Audit bei Kunden prüft**
 * (`services/audit_pagespeed.py`, Gruppe „screenreader").
 *
 * **Warum `<img>` hier nicht mitgeprüft wird:** Beim Messen kam genau ein
 * Treffer heraus — und der war ein Falschtreffer. In
 * `AcademyAdminLesson.jsx` steht `'Füge Bilder mit <img>-Tags ein.'` als
 * **Hilfetext**, nicht als Markup. Mit der Bedingung „muss ein `src` haben"
 * sind es null echte Fälle. Eine Regel für eine Klasse, die es nicht gibt,
 * wäre ein Wächter ohne Gegenstand.
 *
 * Wie bei den Schaltflächen: Der Test prüft die Regel, nicht die drei
 * Stellen. Der nächste Symbol-Link bekommt sonst wieder keinen Namen.
 */

const SRC = path.join(__dirname, '..');

// Ein Link, dessen ganzer Inhalt aus höchstens vier Zeichen besteht.
const SYMBOLLINK = /<a\b(?![^>]*(?:aria-label|title=))[^>]*>\s*([^<]{1,4})\s*<\/a>/gs;

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

describe('Namen von Symbol-Links', () => {
  test('kein Link zeigt nur ein Zeichen ohne aria-label', () => {
    const namenlos = [];

    for (const datei of dateienSammeln(SRC)) {
      const inhalt = fs.readFileSync(datei, 'utf8');
      for (const treffer of inhalt.matchAll(SYMBOLLINK)) {
        const inhaltDesLinks = treffer[1].trim();
        // Buchstaben oder Ziffern sind selbst schon ein Name („PDF", „AGB").
        if (/[\p{L}\p{N}]/u.test(inhaltDesLinks)) continue;
        namenlos.push(`${path.relative(SRC, datei)}: „${inhaltDesLinks}"`);
      }
    }

    expect(namenlos).toEqual([]);
  });

  test('ein Bild mit src trägt einen Alternativtext', () => {
    // Die Bedingung „mit src" trennt Markup von Hilfetext: In
    // AcademyAdminLesson.jsx steht `<img>` in einem Satz über HTML-Tags.
    const ohneAlt = [];

    for (const datei of dateienSammeln(SRC)) {
      const inhalt = fs.readFileSync(datei, 'utf8');
      for (const treffer of inhalt.matchAll(/<img\b[^>]*>/gs)) {
        const tag = treffer[0];
        if (!/\bsrc\b/.test(tag)) continue;
        if (/\balt=/.test(tag)) continue;
        ohneAlt.push(`${path.relative(SRC, datei)}: ${tag.slice(0, 60)}`);
      }
    }

    expect(ohneAlt).toEqual([]);
  });
});
