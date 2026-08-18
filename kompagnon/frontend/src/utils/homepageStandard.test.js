import { stufeKurz, stufeFuerScore, stufeAnzeige } from './homepageStandard';

// Die Schwellen des Backends (services/audit_criteria.py::LEVELS). Weicht das
// Frontend ab, zeigt derselbe Score im Widget eine andere Stufe als im Bericht.
describe('stufeFuerScore', () => {
  test.each([
    [100, 'Homepage Standard Platin'],
    [95,  'Homepage Standard Platin'],
    [94,  'Homepage Standard Gold'],
    [85,  'Homepage Standard Gold'],
    [84,  'Homepage Standard Silber'],
    [72,  'Homepage Standard Silber'],
    [70,  'Homepage Standard Silber'],
    [69,  'Homepage Standard Bronze'],
    [50,  'Homepage Standard Bronze'],
    [49,  'Nicht konform'],
    [0,   'Nicht konform'],
  ])('Score %i ergibt %s', (score, erwartet) => {
    expect(stufeFuerScore(score)).toBe(erwartet);
  });

  test('die alten Schwellen gelten nicht mehr', () => {
    // 72 hiess im Widget frueher „Gold", im Bericht „Silber".
    expect(stufeFuerScore(72)).toBe('Homepage Standard Silber');
    // 86 hiess im Widget frueher „Platin".
    expect(stufeFuerScore(86)).toBe('Homepage Standard Gold');
  });

  test('fehlende oder unsinnige Werte fallen auf die unterste Stufe', () => {
    expect(stufeFuerScore(undefined)).toBe('Nicht konform');
    expect(stufeFuerScore(null)).toBe('Nicht konform');
    expect(stufeFuerScore('keine Zahl')).toBe('Nicht konform');
  });
});

describe('stufeAnzeige', () => {
  test('die Stufe vom Server gilt, auch wenn sie dem Score widerspricht', () => {
    // Genau der Fall der K.-o.-Regeln: 78 Punkte, aber kein Impressum.
    expect(stufeAnzeige(78, 'Nicht konform')).toBe('Nicht konform ⚠️');
  });

  test('ohne Angabe vom Server wird gerechnet', () => {
    expect(stufeAnzeige(72)).toBe('Homepage Standard Silber 🥈');
  });

  test('eine unbekannte Stufe vom Server wird unveraendert durchgereicht', () => {
    expect(stufeAnzeige(72, 'Sonderstufe')).toBe('Sonderstufe');
  });
});


describe('stufeKurz', () => {
  test('lässt „Homepage Standard" weg', () => {
    expect(stufeKurz(90)).toBe('Gold');
    expect(stufeKurz(96)).toBe('Platin');
  });

  test('„Nicht konform" bleibt, wie es ist', () => {
    expect(stufeKurz(10)).toBe('Nicht konform');
  });

  test('die Stufe vom Server gilt auch hier', () => {
    // Nur sie kennt die K.-o.-Regeln, die eine Seite unabhängig vom Score
    // deckeln — kein Impressum, kein TLS.
    expect(stufeKurz(96, 'Homepage Standard Bronze')).toBe('Bronze');
  });
});
