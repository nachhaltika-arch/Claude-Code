import { befundZeilen, geprueftAmText } from './anreicherung';

describe('befundZeilen', () => {
  test('macht aus den Befunden lesbare Zeilen', () => {
    const zeilen = befundZeilen({
      has_ssl: true, has_impressum: false, pagespeed_mobile: 43,
    });

    expect(zeilen).toEqual([
      { schluessel: 'ssl',       beschriftung: 'SSL',       wert: 'vorhanden',   art: 'gut' },
      { schluessel: 'impressum', beschriftung: 'Impressum', wert: 'fehlt',       art: 'fehlt' },
      { schluessel: 'pagespeed', beschriftung: 'PageSpeed', wert: '43/100',      art: 'fehlt' },
    ]);
  });

  test('ungeprüft ist nicht dasselbe wie nicht vorhanden', () => {
    const zeilen = befundZeilen({ has_ssl: null, has_impressum: null, pagespeed_mobile: null });

    expect(zeilen.map(z => z.wert)).toEqual(['nicht geprüft', 'nicht geprüft', 'nicht geprüft']);
    expect(zeilen.map(z => z.art)).toEqual(['unbekannt', 'unbekannt', 'unbekannt']);
  });

  test('ein fehlender Block ist wie ungeprüft', () => {
    expect(befundZeilen(undefined).map(z => z.art)).toEqual(['unbekannt', 'unbekannt', 'unbekannt']);
  });

  test('PageSpeed ab 50 gilt als brauchbar', () => {
    const [, , pagespeed] = befundZeilen({ pagespeed_mobile: 50 });

    expect(pagespeed.art).toBe('gut');
  });

  test('PageSpeed 0 ist ein Wert, kein fehlender Wert', () => {
    const [, , pagespeed] = befundZeilen({ pagespeed_mobile: 0 });

    expect(pagespeed.wert).toBe('0/100');
    expect(pagespeed.art).toBe('fehlt');
  });
});

describe('geprueftAmText', () => {
  test('nennt den Zeitpunkt, wenn es einen gibt', () => {
    expect(geprueftAmText({ geprueft_am: '14.08.2026' })).toBe('Geprüft am 14.08.2026');
  });

  test('sagt es, wenn noch nie geprüft wurde', () => {
    expect(geprueftAmText({ geprueft_am: null })).toBe('Noch nicht geprüft');
  });

  test('kommt ohne Block klar', () => {
    expect(geprueftAmText(undefined)).toBe('Noch nicht geprüft');
  });

  test('Werte ohne Zeitpunkt sagen genau das', () => {
    // Die alten Befunde stammen aus der Notizzeile, die keinen Zeitpunkt
    // trug. „Noch nicht geprüft" wäre falsch, ein erfundenes Datum schlimmer.
    expect(geprueftAmText({ geprueft_am: null, has_ssl: true }))
      .toBe('Geprüft — Zeitpunkt unbekannt');
  });

  test('auch ein PageSpeed von 0 zählt als Wert', () => {
    expect(geprueftAmText({ geprueft_am: null, pagespeed_mobile: 0 }))
      .toBe('Geprüft — Zeitpunkt unbekannt');
  });

  test('ein has_ssl von false ist ebenfalls ein Wert', () => {
    expect(geprueftAmText({ geprueft_am: null, has_ssl: false }))
      .toBe('Geprüft — Zeitpunkt unbekannt');
  });
});
