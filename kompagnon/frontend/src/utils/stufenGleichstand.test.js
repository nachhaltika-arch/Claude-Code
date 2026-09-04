/**
 * Die Stufen des Homepage Standards stehen an drei Orten (BUCH-12, FIX-5).
 *
 * **Warum das gefährlich ist — und zwar bald mehr als heute.** Sobald das Buch
 * gedruckt ist, sind diese Zahlen in Papier gegossen. Eine Änderung an einer
 * Stelle, die nicht überall nachgezogen wird, macht das Buch falsch, und es
 * fällt erst auf, wenn ein Kunde nachrechnet.
 *
 * **Die drei Orte, am 29.08.2026 nachgemessen:**
 *
 *     backend/services/audit_katalog.py    LEVELS          — die Quelle
 *       (bis 30.08.2026 in `audit_criteria.py`; der Katalog ist seither
 *        nach Form, Inhalt und Rechnung geteilt — L-25)
 *     frontend/src/utils/homepageStandard  STUFEN          — fürs Werkzeug
 *     frontend/public/embed/audit-widget.html              — fürs Widget
 *
 * **Warum drei und nicht eine.** Das Backend rechnet in Python, das Werkzeug
 * in React, und das Widget läuft auf **fremden Seiten** als eine Datei ohne
 * Bauschritt — es kann nichts importieren. Zusammenlegen geht also nicht; was
 * geht, ist eine Prüfung, die Abweichungen meldet. BUCH-12 verlangt genau das:
 * *„Für audit-widget.html (kein Build) zumindest ein Prüfskript, das
 * Abweichungen meldet."*
 *
 * **Der Befund, den das schon einmal gekostet hat** (steht im Kopf von
 * `homepageStandard.js`): Das Backend staffelte 95/85/70/50, Widget und
 * Akquise-Haken 85/70/50/30. Derselbe Score hieß im Bericht „Silber" und im
 * Widget „Gold" — ein stiller Fehler mit direkter Außenwirkung, weil beides
 * beim selben Empfänger ankommt.
 *
 * **Die Stufennamen prüft dieser Wächter mit.** Sie stehen in fünf weiteren
 * Dateien als Schlüssel von Farbtabellen (`AuditReport`, `AuditTool`,
 * `LeadProfile`, `CustomerDashboard`, `CustomerPortal`). Die zusammenzulegen
 * wäre eine Gestaltungsänderung; sie beim Umbenennen **auffallen** zu lassen,
 * kostet nichts — und ohne das verlöre eine umbenannte Stufe still ihre Farbe.
 */
import fs from 'fs';
import path from 'path';

import { STUFEN } from './homepageStandard';

const WURZEL = path.join(__dirname, '..', '..', '..');
const KATALOG = path.join(WURZEL, 'backend', 'services', 'audit_katalog.py');
const WIDGET = path.join(WURZEL, 'frontend', 'public', 'embed',
                         'audit-widget.html');

/** `(95, "Homepage Standard Platin"),` → `[95, 'Homepage Standard Platin']` */
function ausKatalog() {
  const text = fs.readFileSync(KATALOG, 'utf8');
  const block = text.match(/LEVELS[^=]*=\s*\(([\s\S]*?)\n\)/);
  if (!block) throw new Error('LEVELS in audit_katalog.py nicht gefunden');
  return [...block[1].matchAll(/\(\s*(\d+)\s*,\s*"([^"]+)"\s*\)/g)]
    .map((m) => [Number(m[1]), m[2]]);
}

/** `if (s >= 95) return 'Homepage Standard Platin 💎';` */
function ausWidget() {
  const text = fs.readFileSync(WIDGET, 'utf8');
  return [...text.matchAll(
    /if\s*\(\s*s\s*>=\s*(\d+)\s*\)\s*return\s*'([^']+)'/g)]
    .map((m) => [Number(m[1]), m[2].replace(/\s*\p{Emoji_Presentation}.*$/u, '')
      .trim()]);
}

describe('Die drei Quellen sagen dasselbe', () => {
  test('der Katalog wird überhaupt gelesen', () => {
    // Ohne diese Zusicherung wäre alles grün, sobald sich das Muster ändert
    // und die Auswertung leer zurückkommt — ein Wächter ohne Wirkung.
    expect(ausKatalog().length).toBeGreaterThanOrEqual(4);
  });

  test('das Widget wird überhaupt gelesen', () => {
    expect(ausWidget().length).toBeGreaterThanOrEqual(4);
  });

  test('Backend und Werkzeug staffeln gleich', () => {
    // Arrange
    const katalog = ausKatalog();

    // Act
    const werkzeug = STUFEN.map((s) => [s.ab, s.name]);

    // Assert
    expect(werkzeug).toEqual(katalog);
  });

  test('das Widget staffelt wie das Backend', () => {
    // Das Widget läuft auf fremden Seiten und kann nichts importieren.
    // Arrange
    const katalog = ausKatalog().filter(([ab]) => ab > 0);

    // Act
    const widget = ausWidget();

    // Assert
    expect(widget).toEqual(katalog);
  });

  test('die Stufennamen der Farbtabellen sind noch die geltenden', () => {
    // Fünf Dateien führen Farben je Stufenname. Wird eine Stufe umbenannt,
    // verliert sie dort still ihre Farbe — die Tabelle greift dann ins Leere.
    const dateien = [
      // Seit dem 30.08.2026 steht `LEVEL_STYLES` in `audit/auditDaten.jsx`:
      // Der Bericht ist geteilt (L-25). Die Berichtsdatei bleibt in der Liste,
      // damit eine Farbtabelle, die dorthin zurueckwandert, wieder mitgeprueft
      // wird.
      'components/audit/auditDaten.jsx',
      'components/AuditReport.jsx',
      'pages/AuditTool.jsx',
      'pages/LeadProfile.jsx',
      'pages/CustomerDashboard.jsx',
      'pages/CustomerPortal.jsx',
    ];
    const gueltig = new Set(STUFEN.map((s) => s.name));

    const unbekannt = [];
    dateien.forEach((datei) => {
      const text = fs.readFileSync(path.join(__dirname, '..', datei), 'utf8');
      [...text.matchAll(/'(Homepage Standard [A-Za-zÄÖÜäöüß]+)'\s*:/g)]
        .forEach((m) => {
          if (!gueltig.has(m[1])) unbekannt.push(`${datei}: ${m[1]}`);
        });
    });

    expect(unbekannt).toEqual([]);
  });

  test('jede Stufe kommt in mindestens einer Farbtabelle vor', () => {
    // Die Gegenprobe: Ohne sie bliebe die Prüfung oben auch dann grün, wenn
    // eine **neue** Stufe nirgends eingetragen wurde — sie sähe dann überall
    // farblos aus, und niemand merkte es.
    // **Am 30.08.2026 nachgezogen.** Hier stand `components/AuditReport.jsx`,
    // und dieser Test wurde rot, als die Stufentabelle beim Teilen des
    // Berichts nach `audit/auditDaten.jsx` zog (L-25) — richtig so: Er sucht
    // die Tabelle, nicht die Datei, und sagt es, wenn sie nicht mehr da ist.
    const text = fs.readFileSync(
      path.join(__dirname, '..', 'components/audit/auditDaten.jsx'), 'utf8');

    STUFEN.filter((s) => s.ab > 0).forEach((stufe) => {
      expect(text).toContain(`'${stufe.name}'`);
    });
  });
});
