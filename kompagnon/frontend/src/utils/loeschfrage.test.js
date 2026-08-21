import { anzahlWort, loeschfrage } from './loeschfrage';

test('ohne Anhang bleibt die Frage kurz', () => {
  expect(loeschfrage('Lektion', 'Erste Schritte'))
    .toBe('Lektion „Erste Schritte" löschen?');
});

test('mit Anhang steht dabei, was mitgeht', () => {
  expect(loeschfrage('Modul', 'Grundlagen', [[3, 'Lektion', 'Lektionen']]))
    .toBe('Modul „Grundlagen" löschen?\n\nDamit geht auch: 3 Lektionen.');
});

test('ein leerer Anhang wird nicht erwähnt', () => {
  // „Damit geht auch: 0 Lektionen" wäre schlechter als nichts.
  expect(loeschfrage('Modul', 'Leer', [[0, 'Lektion', 'Lektionen']]))
    .toBe('Modul „Leer" löschen?');
});

test('die Einzahl wird richtig gebeugt', () => {
  expect(anzahlWort(1, 'Lektion', 'Lektionen')).toBe('1 Lektion');
  expect(anzahlWort(2, 'Lektion', 'Lektionen')).toBe('2 Lektionen');
});

test('ohne Namen geht es auch', () => {
  expect(loeschfrage('Version')).toBe('Version löschen?');
});
