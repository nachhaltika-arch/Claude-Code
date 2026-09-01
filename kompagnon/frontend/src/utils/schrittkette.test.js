/**
 * Die Schrittkette — sie entscheidet, welcher Schritt erreichbar ist.
 *
 * Ein Fehler hier sperrt ein ganzes Projekt, ohne dass etwas kaputt aussieht:
 * Die Seitenleiste zeigt Schlösser, der Nutzer kommt nicht weiter, und nichts
 * meldet einen Fehler. Beim Einfügen der beiden Legacy-Schritte am 21.08.2026
 * wäre genau das passiert — ein neuer, unbestätigter Schritt an Position 3
 * hätte jedes laufende Projekt dort festgehalten.
 */
import { computeStepStatus } from '../utils/schrittkette';
import { SCHRITTE } from '../components/KASSidebar';

const LEERES_PROJEKT = {};
// `content_analysiert_am` statt `scrape_full_at` (26.08.2026): Das alte
// Feld stand in der Datenbank, kam aber nie ueber die Schnittstelle — die
// Kette las hier `undefined`. Dieser Test war gruen, weil **er** das Feld
// selbst setzte; die Oberflaeche bekam es nie. Ein Testdatensatz, den es so
// draussen nicht gab.
const FERTIGE_ANALYSE = { has_briefing: true, audit_score: 72, content_analysiert_am: '2026-08-20T09:00:00' };

describe('Schrittnummern', () => {
  test('sind lückenlos und folgen der Reihenfolge', () => {
    // Arrange & Act
    const nummern = SCHRITTE.map((s) => s.nr);

    // Assert
    expect(nummern).toEqual(SCHRITTE.map((_, i) => i + 1));
  });

  test('jede Kennung kommt genau einmal vor', () => {
    const kennungen = SCHRITTE.map((s) => s.id);
    expect(new Set(kennungen).size).toBe(kennungen.length);
  });
});

describe('Optionale Schritte', () => {
  test('reißen die Kette nicht ab', () => {
    // `zugangsdaten` (optional) hat keine Heuristik und ist nie 'completed'.
    // Vorher blieb die Kette dort stehen und alles dahinter war gesperrt.
    const status = computeStepStatus(FERTIGE_ANALYSE, {}, {});

    expect(status['zugangsdaten']).not.toBe('locked');
    expect(status['sitemap-ki']).not.toBe('locked');
  });

  test('die beiden Legacy-Schritte sperren nichts', () => {
    // Arrange — ein Projekt, das die Analyse hinter sich hat
    const status = computeStepStatus(FERTIGE_ANALYSE, {}, {});

    // Assert — GEO steht an Position 3, Leistungsseiten an 9
    expect(status['geo-optimierung']).not.toBe('locked');
    expect(status['content-vollanalyse']).toBe('completed');
    expect(status['briefing-website']).toBe('completed');
  });
});

describe('Die Sperre selbst', () => {
  test('greift weiterhin für Pflichtschritte', () => {
    // Ohne Briefing ist Schritt 1 offen, Schritt 2 bereit — der Rest gesperrt.
    const status = computeStepStatus(LEERES_PROJEKT, {}, {});

    expect(status['briefing-unternehmen']).toBe('ready');
    expect(status['netlify-deploy']).toBe('locked');
    expect(status['abnahme']).toBe('locked');
  });

  test('eine Bestätigung des Nutzers schlägt die Heuristik', () => {
    const status = computeStepStatus(
      LEERES_PROJEKT, {}, { 'briefing-unternehmen': { confirmed: true } },
    );

    expect(status['briefing-unternehmen']).toBe('completed');
    expect(status['audit']).toBe('ready');
  });

  test('ohne Projekt gibt es keinen Zustand', () => {
    expect(computeStepStatus(null, {}, {})).toEqual({});
  });
});

describe('Jeder Schritt kann etwas anzeigen', () => {
  test('jeder Schritt hat eine Ansicht, eine Komponente — oder ist Platzhalter', () => {
    // Ein Schritt ohne beides ist ein Menüpunkt, hinter dem nichts steht.
    // Erlaubt ist das nur für die drei Post-Launch-Schritte, die noch keine
    // Anbindung haben; sie zeigen einen erklärenden Text.
    const leer = SCHRITTE.filter((s) => !s.view && !s.component).map((s) => s.id);

    expect(leer).toEqual(['umami', 'heatmap', 'monats-report']);
  });
});

// ── Kein neuer Schritt darf die Kette abreißen ───────────────────────
//
// **Zum zweiten Mal passiert, am 01.09.2026.** Der Kopf dieser Datei
// beschreibt den Fall vom 21.08. — und beim Einfügen von „Drei Entwürfe"
// (L-105) ist er trotzdem wieder eingetreten: kein Eintrag in
// `computeStepStatus`, kein `optional`, und damit war alles dahinter gesperrt,
// auch die Design-Ansicht.
//
// **Gefangen hat es der E2E-Lauf**, also die teuerste und letzte Stelle: Der
// Browsertest „Entwurf auf die Seite übernehmen" fand den Knopf gesperrt vor.
// Die Tests hier oben liefen grün, weil sie feste Schritte prüfen — nicht die
// Regel dahinter.
//
// Diese Prüfung ist die frühe Stelle: Sie gilt für **jeden** Schritt, auch für
// den, den es noch nicht gibt.

describe('Neue Schritte', () => {
  /** Welche Kennungen `computeStepStatus` **ausdrücklich** zuweist.
   *
   * **Gelesen wird der Quelltext, und das ist hier keine Bequemlichkeit.**
   * Der erste Entwurf nahm `Object.keys(computeStepStatus(...))` — und war
   * grün, egal was man einfügte: Die Sperrschleife am Ende der Funktion
   * vergibt **jedem** Schritt einen Status, also steht jede Kennung in den
   * Schlüsseln. Der Wächter maß seine eigene Schleife statt der Heuristik.
   *
   * Aufgefallen ist es nur an der Gegenprobe. Eine Zusicherung ohne sie wäre
   * hier grün geblieben und hätte den Fehler beim nächsten Mal wieder
   * durchgelassen.
   */
  function mitHeuristik() {
    const fs = require('fs');
    const path = require('path');
    const quelle = fs.readFileSync(
      path.join(__dirname, 'schrittkette.js'), 'utf8');
    // Nur die Zuweisungen oberhalb der Sperrschleife zählen.
    const vorDerSperre = quelle.split('let consecutiveDoneIdx')[0];
    return new Set(
      [...vorDerSperre.matchAll(/status\['([a-z-]+)'\]\s*=/g)].map((m) => m[1]),
    );
  }

  test('jeder Schritt hat eine Heuristik oder ist als optional gekennzeichnet', () => {
    const bekannt = mitHeuristik();

    const reisser = SCHRITTE
      .filter((s) => !bekannt.has(s.id) && !s.optional)
      .map((s) => s.id);

    expect(reisser).toEqual([]);
  });

  test('ein Schritt ohne beides würde die Kette wirklich abreißen', () => {
    // **Die positive Gegenprobe.** Ohne sie wäre der Test oben auch grün,
    // wenn die Sperrlogik verschwände — dann reißt kein Schritt mehr etwas
    // ab, weil es nichts mehr abzureißen gibt.
    const status = computeStepStatus({}, {}, {});

    // `briefing-unternehmen` ist ohne Briefing nicht erledigt und nicht
    // optional; alles ab dem übernächsten Schritt muss gesperrt sein.
    expect(status['briefing-unternehmen']).toBe('ready');
    expect(status['briefing-website']).toBe('locked');
  });
});
