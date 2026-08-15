/**
 * Die Eigenprüfung im Editor — was der Knopf auslöst und was er zeigt.
 *
 * Die Prüfung misst den Stand, der in der Datenbank liegt, nicht den im
 * Browser. Wer im Editor etwas ändert und dann prüft, würde sonst den
 * vorigen Stand bewertet bekommen und die Bewertung auf seine ungesicherte
 * Arbeit beziehen. Deshalb steht hier zuerst, dass gespeichert wird.
 */
import {
  MELDUNGEN,
  fehlermeldung,
  istEndzustand,
  pruefungAbgeschlossen,
  zusammenfassung,
} from './qualitaetspruefung';

describe('fehlermeldung', () => {
  test('nennt bei fehlender Einrichtung, was einzurichten ist', () => {
    // Arrange
    const detail = 'NETLIFY_VORSCHAU_SITE_ID ist nicht gesetzt.';

    // Act
    const text = fehlermeldung(503, detail);

    // Assert
    expect(text).toContain('Vorschau-Site');
  });

  test('erklärt eine leere Seite, statt einen Fehler zu melden', () => {
    expect(fehlermeldung(400, 'weder Editorstand noch Entwurf')).toBe(
      MELDUNGEN.leer,
    );
  });

  test('trennt ein Netlify-Problem von einem eigenen Fehler', () => {
    expect(fehlermeldung(502, 'Netlify Deploy Fehler')).toBe(MELDUNGEN.deploy);
  });

  test('fällt bei unbekanntem Status auf eine brauchbare Meldung zurück', () => {
    expect(fehlermeldung(500, '')).toBe(MELDUNGEN.unbekannt);
  });
});

describe('istEndzustand', () => {
  test('läuft weiter bei pending und running', () => {
    expect(istEndzustand('pending')).toBe(false);
    expect(istEndzustand('running')).toBe(false);
  });

  test('hört bei completed und failed auf', () => {
    expect(istEndzustand('completed')).toBe(true);
    expect(istEndzustand('failed')).toBe(true);
  });

  test('hört auch bei unbekanntem Zustand auf, statt ewig zu fragen', () => {
    expect(istEndzustand('')).toBe(true);
    expect(istEndzustand(undefined)).toBe(true);
  });
});

describe('pruefungAbgeschlossen', () => {
  test('meldet Erfolg nur bei completed', () => {
    expect(pruefungAbgeschlossen({ status: 'completed' })).toBe(true);
    expect(pruefungAbgeschlossen({ status: 'failed' })).toBe(false);
  });
});

describe('zusammenfassung', () => {
  test('nennt Punktzahl und Stufe des Servers', () => {
    // Arrange
    const audit = { total_score: 62, level: 'Homepage Standard Bronze', coverage: 98 };

    // Act
    const s = zusammenfassung(audit);

    // Assert
    expect(s.punkte).toBe(62);
    expect(s.stufe).toContain('Bronze');
    expect(s.abdeckung).toBe(98);
  });

  test('übernimmt die Stufe des Servers, statt sie nachzurechnen', () => {
    // Der Server kennt die K.-o.-Regeln, die eine Seite unabhängig vom
    // Punktestand deckeln — kein Impressum, kein TLS.
    const s = zusammenfassung({ total_score: 92, level: 'Nicht konform' });

    expect(s.stufe).toContain('Nicht konform');
  });

  test('kommt mit einem leeren Ergebnis zurecht', () => {
    const s = zusammenfassung(null);

    expect(s.punkte).toBe(0);
    expect(s.stufe).toBeTruthy();
  });

  test('färbt nach Punktzahl, damit die Anzeige ohne Lesen wirkt', () => {
    expect(zusammenfassung({ total_score: 90 }).ampel).toBe('gut');
    expect(zusammenfassung({ total_score: 60 }).ampel).toBe('mittel');
    expect(zusammenfassung({ total_score: 30 }).ampel).toBe('schwach');
  });
});
