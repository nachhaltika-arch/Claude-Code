import {
  umschalten,
  alleGewaehlt,
  alleUmschalten,
  vorschauZeilen,
  loeschFrage,
} from './projektAuswahl';

describe('umschalten', () => {
  test('nimmt eine ungewählte Nummer auf', () => {
    expect(umschalten([1, 2], 3)).toEqual([1, 2, 3]);
  });

  test('entfernt eine bereits gewählte Nummer', () => {
    expect(umschalten([1, 2, 3], 2)).toEqual([1, 3]);
  });

  test('lässt die ursprüngliche Auswahl unberührt', () => {
    const vorher = [1, 2];

    umschalten(vorher, 3);

    expect(vorher).toEqual([1, 2]);
  });
});

describe('alleUmschalten', () => {
  test('wählt alle sichtbaren, wenn noch nicht alle gewählt sind', () => {
    expect(alleUmschalten([1], [1, 2, 3])).toEqual([1, 2, 3]);
  });

  test('leert die Auswahl, wenn schon alle gewählt sind', () => {
    expect(alleUmschalten([1, 2, 3], [1, 2, 3])).toEqual([]);
  });

  test('behält Gewähltes, das gerade nicht sichtbar ist', () => {
    // Nummer 9 steckt hinter einem Filter — sie darf nicht stillschweigend
    // aus der Auswahl fallen, sonst löscht man weniger als man sieht.
    expect(alleUmschalten([9], [1, 2])).toEqual([9, 1, 2]);
  });

  test('eine leere Liste ändert nichts', () => {
    expect(alleUmschalten([1], [])).toEqual([1]);
  });
});

describe('alleGewaehlt', () => {
  test('stimmt, wenn jede sichtbare Nummer gewählt ist', () => {
    expect(alleGewaehlt([1, 2, 9], [1, 2])).toBe(true);
  });

  test('stimmt nicht, wenn eine fehlt', () => {
    expect(alleGewaehlt([1], [1, 2])).toBe(false);
  });

  test('bei nichts Sichtbarem ist nichts vollständig gewählt', () => {
    expect(alleGewaehlt([1], [])).toBe(false);
  });
});

describe('vorschauZeilen', () => {
  const bericht = {
    projekte: 2,
    wird_geloescht: { project_checklists: 14, customers: 1, invoices: 0 },
    bleibt_erhalten: { email_logs: 135, briefings: 0 },
  };

  test('nennt nur, was tatsächlich betroffen ist', () => {
    const { geloescht } = vorschauZeilen(bericht);

    expect(geloescht.map(z => z.tabelle)).toEqual(['project_checklists', 'customers']);
  });

  test('übersetzt die Tabellennamen', () => {
    const { geloescht } = vorschauZeilen(bericht);

    expect(geloescht[0].beschriftung).toBe('Checklisten');
    expect(geloescht[1].beschriftung).toBe('Kundendaten');
  });

  test('nennt auch, was stehen bleibt', () => {
    const { bleibt } = vorschauZeilen(bericht);

    expect(bleibt).toEqual([
      { tabelle: 'email_logs', beschriftung: 'Versandprotokoll', anzahl: 135 },
    ]);
  });

  test('eine unbekannte Tabelle behält ihren Namen', () => {
    const { geloescht } = vorschauZeilen({
      projekte: 1, wird_geloescht: { irgendwas_neues: 3 }, bleibt_erhalten: {},
    });

    expect(geloescht[0].beschriftung).toBe('irgendwas_neues');
  });

  test('kommt mit einem leeren Bericht klar', () => {
    expect(vorschauZeilen(null)).toEqual({ geloescht: [], bleibt: [] });
  });
});

describe('loeschFrage', () => {
  test('nennt bei einem Projekt dessen Namen', () => {
    expect(loeschFrage(['Muster GmbH'])).toBe('„Muster GmbH" löschen?');
  });

  test('zählt bei mehreren', () => {
    expect(loeschFrage(['A', 'B', 'C'])).toBe('3 Projekte löschen?');
  });

  test('ohne Auswahl gibt es nichts zu fragen', () => {
    expect(loeschFrage([])).toBe('');
  });
});
