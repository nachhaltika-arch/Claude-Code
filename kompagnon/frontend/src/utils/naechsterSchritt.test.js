/**
 * Der nächste Schritt auf der Kundenübersicht (L-161, Wunsch David 04.09.2026).
 *
 * **Warum die Reihenfolge bewacht wird und nicht nur das Ergebnis.** Der
 * Streifen zeigt **einen** Schritt. Welcher es ist, entscheidet über die
 * Bauzeit: Offene Angaben halten sie an, offene Freigaben ebenso (M7/M8).
 * Zeigte die Seite dem Kunden das Guthaben, während wir auf seine Texte
 * warten, verlöre er Tage — und wir die Frist.
 *
 * **Und der vierte Fall ist der, den man vergisst.** Liegt nichts beim
 * Kunden, muss trotzdem etwas dastehen. „Bei Ihnen liegt nichts" ist eine
 * Auskunft, aber keine Antwort auf „und was passiert gerade?".
 */
import { aufgabeBestimmen, lageBestimmen, verlaufBauen } from './kundenuebersicht';

const LAGE_BAU = { zustand: 'bau' };
const LAGE_NACH = { zustand: 'nach' };

const MITWIRKUNG_OFFEN = {
  offen: 2, erledigt: 4, gesamt: 6,
  punkte: [
    { kennung: 'M1', titel: 'Ihre Internet-Adresse', erledigt: true },
    { kennung: 'M2', titel: 'Ihre Texte', erledigt: false },
    { kennung: 'M3', titel: 'Ihre Bilder', erledigt: false },
  ],
};
const MITWIRKUNG_FERTIG = { offen: 0, erledigt: 6, gesamt: 6, punkte: [] };

describe('Welcher Schritt angezeigt wird', () => {
  test('offene Angaben schlagen alles andere — sie halten die Bauzeit an', () => {
    // Arrange — gleichzeitig eine offene Freigabe und freies Guthaben.
    const projekt = { content_freigaben: { startseite: { status: 'angefragt' } } };
    const inhalt = { guthaben: { rest_minuten: 45 } };

    // Act
    const schritt = aufgabeBestimmen({
      lage: LAGE_NACH, mitwirkung: MITWIRKUNG_OFFEN, inhalt, projekt, portal: null,
    });

    // Assert — und zwar der **erste** offene Punkt, nicht irgendeiner.
    expect(schritt.ziel).toBe('/app/was-wir-brauchen');
    expect(schritt.hervor).toBe('Ihre Texte');
    expect(schritt.dazu).toContain('2 von 6');
  });

  test('bei genau einer offenen Angabe wird nicht gezählt, sondern zugesagt', () => {
    // Arrange
    const mitwirkung = { ...MITWIRKUNG_OFFEN, offen: 1 };

    // Act
    const schritt = aufgabeBestimmen({ lage: LAGE_BAU, mitwirkung, inhalt: null, projekt: null, portal: null });

    // Assert
    expect(schritt.dazu).toBe('Danach beginnt die Bauzeit.');
  });

  test('sind die Angaben vollständig, kommen die Freigaben', () => {
    // Arrange — eine ist schon entschieden und zählt nicht mehr.
    const projekt = { content_freigaben: {
      startseite: { status: 'angefragt' },
      leistungen: { status: 'angefragt' },
      kontakt: { status: 'freigegeben' },
    } };

    // Act
    const schritt = aufgabeBestimmen({
      lage: LAGE_BAU, mitwirkung: MITWIRKUNG_FERTIG, inhalt: null, projekt, portal: null,
    });

    // Assert
    expect(schritt.ziel).toBe('/app/freigaben');
    expect(schritt.dazu).toContain('2 Seiten');
    expect(schritt.dazu).toContain('ein Klick je Zeile');
  });

  test('eine einzelne Freigabe steht im Singular da', () => {
    // Arrange
    const projekt = { content_freigaben: { startseite: { status: 'angefragt' } } };

    // Act
    const schritt = aufgabeBestimmen({
      lage: LAGE_BAU, mitwirkung: MITWIRKUNG_FERTIG, inhalt: null, projekt, portal: null,
    });

    // Assert
    expect(schritt.dazu).toContain('1 Seite wartet');
  });

  test('nach dem Go-live führt das freie Guthaben', () => {
    // Arrange
    const inhalt = { guthaben: { rest_minuten: 45, kontingent_minuten: 90 } };

    // Act
    const schritt = aufgabeBestimmen({
      lage: LAGE_NACH, mitwirkung: MITWIRKUNG_FERTIG, inhalt, projekt: null, portal: null,
    });

    // Assert
    expect(schritt.ziel).toBe('/app/inhaltsaenderungen');
    expect(schritt.hervor).toBe('45 Minuten');
  });

  test('liegt nichts beim Kunden, sagt der Streifen woran wir sind — ohne Knopf', () => {
    // Arrange
    const portal = { phases: [
      { number: 1, label: 'Kickoff & Strategie', description: 'Ziele und Sitemap', state: 'done' },
      { number: 2, label: 'Design & Entwurf', description: 'Der Bauplan entsteht', state: 'active' },
      { number: 3, label: 'Umsetzung', state: 'open' },
    ] };

    // Act
    const schritt = aufgabeBestimmen({
      lage: LAGE_BAU, mitwirkung: MITWIRKUNG_FERTIG, inhalt: null, projekt: null, portal,
    });

    // Assert — ein Knopf ohne Aufgabe dahinter wird einmal gedrückt und
    // danach nicht mehr ernst genommen.
    expect(schritt.knopf).toBeNull();
    expect(schritt.ziel).toBeNull();
    expect(schritt.hervor).toBe('Design & Entwurf');
    expect(schritt.dazu).toContain('Schritt 2 von 3');
  });

  test('ohne jede Angabe bleibt der Streifen weg statt leer dazustehen', () => {
    expect(aufgabeBestimmen({
      lage: LAGE_BAU, mitwirkung: null, inhalt: null, projekt: null, portal: null,
    })).toBeNull();
  });
});

describe('Die Lage in einem Satz', () => {
  test('offene Angaben werden ausgeschrieben, nicht gezählt', () => {
    const lage = lageBestimmen({ profil: { projects: [{ status: 'phase_1' }] },
                                 mitwirkung: MITWIRKUNG_OFFEN });
    expect(lage.zustand).toBe('vor');
    expect(lage.satz).toContain('zwei Angaben');
  });

  test('ist alles da, sagt sie das auch', () => {
    const lage = lageBestimmen({ profil: { projects: [{ status: 'phase_2' }] },
                                 mitwirkung: MITWIRKUNG_FERTIG });
    expect(lage.zustand).toBe('bau');
    expect(lage.satz).toContain('Bei Ihnen liegt gerade nichts');
  });

  test('nach dem Go-live ist die Seite online', () => {
    const lage = lageBestimmen({ profil: { projects: [{ status: 'phase_4' }] },
                                 mitwirkung: MITWIRKUNG_FERTIG });
    expect(lage.zustand).toBe('nach');
  });
});

describe('Zuletzt passiert', () => {
  test('mischt die Quellen und zeigt das Jüngste zuerst', () => {
    // Arrange
    const inhalt = { guthaben: { eintraege: [
      { taetigkeit: 'Team-Foto getauscht', minuten: 15, erfasst_am: '2026-09-04T11:00:00' },
    ] } };
    const zahlungen = { rechnungen: [
      { line_item: 'Pflege Pro August', paid_at: '2026-08-12T00:00:00' },
      { line_item: 'Pflege Pro September', paid_at: null },
    ] };
    const profil = { audits: [{ created_at: '2026-09-01T00:00:00' }] };

    // Act
    const zeilen = verlaufBauen({ inhalt, zahlungen, profil });

    // Assert — und die unbezahlte Rechnung ist kein Ereignis.
    expect(zeilen).toHaveLength(3);
    expect(zeilen[0].was).toContain('Team-Foto');
    expect(zeilen.map((z) => z.was).join(' ')).not.toContain('September');
  });

  test('ohne Quellen bleibt die Liste leer statt zu erfinden', () => {
    expect(verlaufBauen({ inhalt: null, zahlungen: null, profil: null })).toEqual([]);
  });
});

describe('Der zugesagte Fertigstellungstag kommt aus der Frist, nicht aus der Planung', () => {
  /**
   * **Der Befund vom 06.09.2026.** Seit L-166 rechnet das Backend ein
   * Bauzeitende — Fristbeginn plus die Bauzeit des gekauften Pakets plus die
   * Ruhezeiten aus verspäteten Freigaben. Es liegt seither in der Antwort von
   * `/api/portal/mitwirkung`, die diese Seite ohnehin abruft.
   *
   * **Benutzt wurde es nicht.** Die Übersicht zeigte weiter
   * `projekt.target_go_live` — ein Feld, das jemand von Hand setzt. Zwei
   * Daten für dieselbe Zusage, und das von Hand gesetzte gewinnt: genau die
   * Klasse „gebaut, nicht angeschlossen", diesmal an meiner eigenen Arbeit
   * von heute Morgen.
   *
   * **Warum das gerechnete gewinnt.** Der Kunde fragt „wann ist es fertig?",
   * und die Antwort darauf ist die **Zusage** aus seinem Vertrag. Eine
   * interne Planung, die früher liegt, wäre ein Versprechen, das niemand
   * gegeben hat; eine, die später liegt, verschweigt die Zusage.
   */
  const projektMitPlanung = {
    profil: { projects: [{ status: 'phase_2', target_go_live: '2026-10-14T00:00:00' }] },
  };

  test('das gerechnete Ende schlägt die von Hand gesetzte Planung', () => {
    const lage = lageBestimmen({
      ...projektMitPlanung,
      mitwirkung: { offen: 0, erledigt: 8, gesamt: 8,
                    frist: { ende: '2026-09-30', pause_werktage: 0 } },
    });

    expect(lage.zustand).toBe('bau');
    // `datum()` schreibt „30. Sept." — meine erste Erwartung stand auf
    // „30.09.2026" und war schlicht falsch abgelesen.
    expect(lage.dazu).toContain('30. Sept');
    expect(lage.dazu).not.toContain('Okt');
    expect(lage.dazu).not.toContain('..');
  });

  test('ohne gerechnetes Ende bleibt die Planung stehen', () => {
    // Kein Rückschritt für Projekte, deren Mitwirkung noch nicht vollständig
    // erfasst ist — dort gibt es keinen Fristbeginn und also kein Ende.
    const lage = lageBestimmen({
      ...projektMitPlanung,
      mitwirkung: { offen: 0, erledigt: 8, gesamt: 8, frist: { ende: null } },
    });

    expect(lage.dazu).toContain('14. Okt');
  });

  test('eine Ruhezeit wird benannt, nicht stillschweigend eingerechnet', () => {
    // Sonst verschöbe sich der zugesagte Tag, und der Kunde läse nur ein
    // neues Datum — ohne zu erfahren, dass seine eigene späte Freigabe es
    // verschoben hat.
    const lage = lageBestimmen({
      ...projektMitPlanung,
      mitwirkung: { offen: 0, erledigt: 8, gesamt: 8,
                    frist: { ende: '2026-10-03', pause_werktage: 3 } },
    });

    expect(lage.dazu).toContain('3. Okt');
    expect(lage.dazu).toMatch(/drei Werktage|3 Werktage/);
  });
});
