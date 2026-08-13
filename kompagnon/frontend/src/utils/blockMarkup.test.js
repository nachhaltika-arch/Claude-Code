import { mitBlockMarkierung } from './blockMarkup';

describe('mitBlockMarkierung', () => {
  test('zieht die Markierung auf den neuen Slug mit', () => {
    // Arrange
    const html = '<section data-block="hero-ki-1" class="py-16"><h1>{{headline}}</h1></section>';

    // Act
    const ergebnis = mitBlockMarkierung(html, 'shk-hero-premium');

    // Assert
    expect(ergebnis).toContain('data-block="shk-hero-premium"');
    expect(ergebnis).not.toContain('hero-ki-1');
  });

  test('markiert nur das Wurzelelement, nicht verschachtelte Treffer', () => {
    const html = '<section data-block="alt"><div data-block="innen">x</div></section>';

    const ergebnis = mitBlockMarkierung(html, 'neu');

    expect(ergebnis).toBe('<section data-block="neu"><div data-block="innen">x</div></section>');
  });

  test('vertraegt Leerzeichen um das Gleichheitszeichen', () => {
    const html = '<section data-block = "alt">x</section>';

    expect(mitBlockMarkierung(html, 'neu')).toBe('<section data-block="neu">x</section>');
  });

  test('erfindet keine Markierung, wenn keine da ist', () => {
    const html = '<section class="py-16">x</section>';

    expect(mitBlockMarkierung(html, 'neu')).toBe(html);
  });

  test('laesst leere Eingaben unveraendert', () => {
    expect(mitBlockMarkierung('', 'neu')).toBe('');
    expect(mitBlockMarkierung('<section data-block="alt">x</section>', '')).toBe(
      '<section data-block="alt">x</section>',
    );
  });
});
