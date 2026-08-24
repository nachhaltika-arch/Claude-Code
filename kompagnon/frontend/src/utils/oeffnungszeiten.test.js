import { oeffnungszeitenAlsJson, oeffnungszeitenAlsText } from './oeffnungszeiten';

/**
 * Öffnungszeiten zwischen Eingabezeilen und gespeichertem JSON (L-15, L-99).
 *
 * `schema.org/LocalBusiness` verlangt sie, und der SEO/GEO-Agent antwortet
 * ohne sie mit 400. Gespeichert wird JSON, eingegeben werden Zeilen — sieben
 * Spalten wären sieben Migrationen beim ersten Sonderfall.
 *
 * Der wichtigste Fall ist der halb getippte: Ein Feld in einem Formular darf
 * die Seite nicht zerlegen, und die Eingabe des Nutzers darf beim ersten
 * Zeichen, das kein gültiges JSON ergibt, nicht verschwinden.
 */
describe('Öffnungszeiten hin und zurück', () => {
  test('ein Verzeichnis wird zu einer Zeile je Eintrag', () => {
    const roh = JSON.stringify({ 'Mo-Do': '08:00-17:00', Fr: '08:00-13:00' });
    expect(oeffnungszeitenAlsText(roh)).toBe('Mo-Do 08:00-17:00\nFr 08:00-13:00');
  });

  test('Zeilen werden zu einem Verzeichnis', () => {
    const text = 'Mo-Do 08:00-17:00\nFr 08:00-13:00';
    expect(JSON.parse(oeffnungszeitenAlsJson(text))).toEqual({
      'Mo-Do': '08:00-17:00', Fr: '08:00-13:00',
    });
  });

  test('hin und zurück ergibt dasselbe', () => {
    const text = 'Mo-Fr 08:00-17:00\nSa nach Vereinbarung';
    expect(oeffnungszeitenAlsText(oeffnungszeitenAlsJson(text))).toBe(text);
  });

  test('leere Eingabe bleibt leer statt „{}" zu speichern', () => {
    expect(oeffnungszeitenAlsJson('')).toBe('');
    expect(oeffnungszeitenAlsJson('   \n  ')).toBe('');
    expect(oeffnungszeitenAlsText('')).toBe('');
    expect(oeffnungszeitenAlsText(null)).toBe('');
  });

  test('ein Eintrag ohne Zeit raet nichts dazu', () => {
    expect(JSON.parse(oeffnungszeitenAlsJson('Sonntag'))).toEqual({ Sonntag: '' });
  });

  test('halb getippter Text verschwindet nicht', () => {
    // Genau der Zustand waehrend des Tippens: noch kein gueltiges JSON.
    expect(oeffnungszeitenAlsText('Mo-Fr 08')).toBe('Mo-Fr 08');
  });

  test('ein Array ist kein Verzeichnis und ergibt nichts', () => {
    expect(oeffnungszeitenAlsText('[1,2,3]')).toBe('');
  });
});
