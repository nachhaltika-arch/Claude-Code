/**
 * Beträge in deutscher Schreibweise (L-101/L-162, 04.09.2026).
 *
 * Der Anlass: Das Pflege-Abo läuft seit dem 04.09. über Stripe, und der
 * Kunde sieht im Konto, was monatlich abgebucht wird. Ein Betrag, der um
 * Faktor hundert danebenliegt, ist kein Schönheitsfehler — er entscheidet,
 * ob jemand den Einzug einrichtet.
 */
import { euro, euroAusCent } from './geld';

// Der geschützte Schmalraum, den `toLocaleString` vor das € setzt.
const raum = (s) => s.replace(/ /g, ' ');

describe('Beträge in Euro', () => {
  test('formatiert mit Punkt für Tausend und Komma für Cent', () => {
    expect(raum(euro(4165))).toBe('4.165,00 €');
  });

  test('zeigt immer zwei Nachkommastellen', () => {
    expect(raum(euro(79))).toBe('79,00 €');
  });
});

describe('Beträge in Cent', () => {
  test('rechnet Cent in Euro um — 9401 ist der Bruttopreis von Pflege Basic', () => {
    expect(raum(euroAusCent(9401))).toBe('94,01 €');
  });

  test('und 17731 der von Pflege Pro', () => {
    expect(raum(euroAusCent(17731))).toBe('177,31 €');
  });

  test('nichts ist nicht NaN', () => {
    // Ein fehlendes Feld darf keinen kaputten Betrag auf den Bildschirm
    // bringen — „NaN €" liest sich wie ein Fehler des Kunden.
    expect(raum(euroAusCent(undefined))).toBe('0,00 €');
    expect(raum(euroAusCent(null))).toBe('0,00 €');
  });
});
