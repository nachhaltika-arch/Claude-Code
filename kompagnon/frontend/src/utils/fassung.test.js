import { fassungText, vergleichbar, fassungenIm } from './fassung';

describe('fassungText', () => {
  test('nennt die Fassung, wenn eine vermerkt ist', () => {
    expect(fassungText('2026.2')).toBe('Fassung 2026.2');
  });

  test('sagt bei fehlendem Vermerk, dass keiner da ist, statt einen zu erfinden', () => {
    expect(fassungText('')).toBe('Fassung nicht vermerkt');
    expect(fassungText(null)).toBe('Fassung nicht vermerkt');
    expect(fassungText(undefined)).toBe('Fassung nicht vermerkt');
  });
});

describe('vergleichbar', () => {
  test('erlaubt den Vergleich bei gleicher Fassung', () => {
    expect(vergleichbar('2026.2', '2026.2')).toBe(true);
  });

  test('verweigert ihn bei verschiedenen Fassungen', () => {
    expect(vergleichbar('2026.1', '2026.2')).toBe(false);
  });

  test('behandelt zwei unbekannte Fassungen nicht als gleich', () => {
    // Arrange / Act / Assert — unbekannt ist keine Uebereinstimmung.
    expect(vergleichbar('', '')).toBe(false);
    expect(vergleichbar(null, undefined)).toBe(false);
  });
});

describe('fassungenIm', () => {
  test('zaehlt jede Fassung einmal', () => {
    const audits = [
      { standard_version: '2026.2' },
      { standard_version: '2026.2' },
      { standard_version: '2026.1' },
    ];
    expect(fassungenIm(audits)).toEqual(['2026.2', '2026.1']);
  });

  test('kommt mit einer leeren Liste zurecht', () => {
    expect(fassungenIm([])).toEqual([]);
    expect(fassungenIm(null)).toEqual([]);
  });
});
