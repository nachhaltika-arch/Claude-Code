import {
  BETRIEB_ANSICHTEN,
  ansichtAnwenden,
  ansichtFinden,
  istEigeneAuswahl,
} from './betriebAnsichten';

/**
 * Benannte Ansichten statt bloßer Filter (L-83).
 *
 * Aus dem HubSpot-Audit vom 19.08.2026: Dort liegen gespeicherte Ansichten
 * als Reiter über der Liste. Bei uns stellt jeder, der täglich dieselbe
 * Auswahl braucht, sie jedes Mal neu ein — Status, Quelle, Phase, Sortierung,
 * vier Entscheidungen für einen Blick, den man zwanzigmal am Tag wirft.
 */

describe('Der Vorrat an Ansichten', () => {
  test('jede Ansicht hat Kennung, Namen und einen vollständigen Filterzustand', () => {
    for (const a of BETRIEB_ANSICHTEN) {
      expect(a.id).toBeTruthy();
      expect(a.label).toBeTruthy();
      // Vollständig heißt: Jede Achse ist gesetzt. Eine Ansicht, die eine
      // Achse offen lässt, erbt den vorigen Zustand — und dann zeigt
      // derselbe Reiter zweimal Verschiedenes.
      expect(a.filter).toMatchObject({
        status: expect.any(String),
        quelle: expect.any(String),
        phase: expect.any(String),
        sortierung: expect.any(String),
      });
    }
  });

  test('die Kennungen sind eindeutig', () => {
    const ids = BETRIEB_ANSICHTEN.map((a) => a.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test('die erste Ansicht zeigt alles — der Einstieg verbirgt nichts', () => {
    const [erste] = BETRIEB_ANSICHTEN;
    expect(erste.filter).toEqual({
      status: 'alle', quelle: 'alle', phase: 'alle', sortierung: 'name',
    });
  });
});

describe('ansichtAnwenden', () => {
  test('setzt den ganzen Filterzustand, nicht einzelne Achsen', () => {
    const vorher = { status: 'won', quelle: 'csv_import', phase: 'kunde',
                     sortierung: 'score', suche: 'meier' };

    const nachher = ansichtAnwenden(vorher, 'neu');

    expect(nachher.status).toBe(BETRIEB_ANSICHTEN.find((a) => a.id === 'neu').filter.status);
    expect(nachher.quelle).toBe('alle');
  });

  test('die Suche bleibt stehen', () => {
    // Wer sucht und dann die Ansicht wechselt, will die Suche behalten —
    // sonst tippt er sie zum zweiten Mal.
    const nachher = ansichtAnwenden({ suche: 'meier' }, 'kunden');

    expect(nachher.suche).toBe('meier');
  });

  test('eine unbekannte Kennung ändert nichts', () => {
    const vorher = { status: 'won', quelle: 'alle', phase: 'alle',
                     sortierung: 'name', suche: '' };

    expect(ansichtAnwenden(vorher, 'gibtesnicht')).toEqual(vorher);
  });

  test('gibt ein neues Objekt zurück und fasst die Eingabe nicht an', () => {
    const vorher = { status: 'won', suche: 'meier' };

    ansichtAnwenden(vorher, 'kunden');

    expect(vorher.status).toBe('won');
  });
});

describe('ansichtFinden — welcher Reiter ist gerade aktiv', () => {
  test('erkennt die Ansicht am Filterzustand', () => {
    const kunden = BETRIEB_ANSICHTEN.find((a) => a.id === 'kunden');

    expect(ansichtFinden({ ...kunden.filter, suche: '' })).toBe('kunden');
  });

  test('die Suche zählt nicht mit', () => {
    const kunden = BETRIEB_ANSICHTEN.find((a) => a.id === 'kunden');

    expect(ansichtFinden({ ...kunden.filter, suche: 'meier' })).toBe('kunden');
  });

  test('eine eigene Zusammenstellung gehört zu keiner Ansicht', () => {
    // Wichtig: Sonst leuchtet ein Reiter, der etwas anderes zeigt als das,
    // was in der Liste steht.
    const eigen = { status: 'won', quelle: 'csv_import', phase: 'kunde',
                    sortierung: 'score' };

    expect(ansichtFinden(eigen)).toBeNull();
    expect(istEigeneAuswahl(eigen)).toBe(true);
  });
});
