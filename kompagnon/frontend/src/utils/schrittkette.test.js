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
