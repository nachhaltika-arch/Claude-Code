import {
  alsDatum,
  istDatum,
  datumKurz,
  datumLang,
  monatUndJahr,
  datumUndZeit,
  nurZeit,
  KEIN_DATUM,
} from './datum';

const ALLE_FORMATE = [datumKurz, datumLang, monatUndJahr, datumUndZeit, nurZeit];

// ── Der Anlass: „Invalid Date" darf nie sichtbar werden ────────────────

describe('kein Format gibt jemals „Invalid Date" aus', () => {
  const kaputteWerte = [
    undefined,
    null,
    '',
    'kein-datum',
    '0000-00-00',
    'Invalid Date',
    {},
    NaN,
    new Date('kaputt'),
  ];

  test.each(kaputteWerte.map(w => [JSON.stringify(w) ?? String(w), w]))(
    'für %s kommt der Ersatztext, nicht „Invalid Date"',
    (_name, wert) => {
      for (const format of ALLE_FORMATE) {
        expect(format(wert)).toBe(KEIN_DATUM);
      }
    },
  );

  test('ein truthy, aber unlesbarer Wert rutscht nicht durch', () => {
    // Genau die Lücke, die der übliche Schutz `x ? … : '—'` offen lässt:
    // die Zeichenkette ist wahr, ergibt aber kein Datum.
    expect(Boolean('0000-00-00')).toBe(true);
    expect(datumKurz('0000-00-00')).toBe(KEIN_DATUM);
  });
});

// ── alsDatum ───────────────────────────────────────────────────────────

describe('alsDatum', () => {
  test('liest einen ISO-Zeitstempel', () => {
    expect(alsDatum('2026-08-17T10:00:00Z').getTime()).toBe(Date.parse('2026-08-17T10:00:00Z'));
  });

  test('liest ein reines Datum', () => {
    expect(alsDatum('2026-08-17')).toBeInstanceOf(Date);
  });

  test('reicht ein gültiges Date durch', () => {
    const datum = new Date('2026-08-17T10:00:00Z');

    expect(alsDatum(datum)).toBe(datum);
  });

  test('weist ein ungültiges Date ab', () => {
    expect(alsDatum(new Date('kaputt'))).toBeNull();
  });

  test('liest einen Zeitstempel in Millisekunden', () => {
    const millis = Date.parse('2026-08-17T10:00:00Z');

    expect(alsDatum(millis).getTime()).toBe(millis);
  });

  test('gibt null für fehlende Werte zurück', () => {
    expect(alsDatum(null)).toBeNull();
    expect(alsDatum(undefined)).toBeNull();
    expect(alsDatum('')).toBeNull();
  });
});

describe('istDatum', () => {
  test('ist wahr für einen lesbaren Wert', () => {
    expect(istDatum('2026-08-17')).toBe(true);
  });

  test('ist falsch für einen unlesbaren Wert', () => {
    expect(istDatum('kein-datum')).toBe(false);
  });
});

// ── Die Formate ────────────────────────────────────────────────────────

describe('Formate', () => {
  const referenz = '2026-08-17T14:32:00Z';

  test('datumKurz schreibt Tag, Monat und Jahr zweistellig', () => {
    expect(datumKurz('2026-08-17T10:00:00Z')).toBe('17.08.2026');
  });

  test('datumLang schreibt den Monat aus', () => {
    expect(datumLang('2026-08-17T10:00:00Z')).toBe('17. August 2026');
  });

  test('monatUndJahr lässt den Tag weg', () => {
    expect(monatUndJahr('2026-08-17T10:00:00Z')).toBe('August 2026');
  });

  test('datumUndZeit nennt beides', () => {
    const text = datumUndZeit(referenz);

    expect(text).toContain('17.08.2026');
    expect(text).toMatch(/\d{2}:\d{2}/);
  });

  test('nurZeit nennt Stunde und Minute', () => {
    expect(nurZeit(referenz)).toMatch(/^\d{2}:\d{2}$/);
  });
});

// ── Ersatztext ─────────────────────────────────────────────────────────

describe('Ersatztext', () => {
  test('ohne Angabe steht dort ein Gedankenstrich', () => {
    expect(datumKurz(null)).toBe('—');
  });

  test('der Aufrufer kann einen eigenen Ersatztext setzen', () => {
    expect(datumKurz(null, 'Datum unbekannt')).toBe('Datum unbekannt');
  });

  test('der Ersatztext gilt auch für unlesbare Werte, nicht nur für fehlende', () => {
    expect(datumKurz('kein-datum', 'Datum unbekannt')).toBe('Datum unbekannt');
  });

  test('ein leerer Ersatztext ist erlaubt, wo die Zeile sonst nichts trägt', () => {
    expect(datumKurz(null, '')).toBe('');
  });
});
