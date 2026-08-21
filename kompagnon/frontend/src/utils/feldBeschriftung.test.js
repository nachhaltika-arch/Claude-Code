/**
 * L-17: Eine Beschriftung, die danebensteht, ist für einen Screenreader
 * keine Beschriftung.
 */
import { beschriftungsText, feldVerknuepfung } from './feldBeschriftung';

describe('feldVerknuepfung', () => {
  test('ein Feld ohne Kennung bekommt die erzeugte', () => {
    // Act
    const { id, verknuepfen, zusatz } = feldVerknuepfung({}, 'r1');

    // Assert
    expect(id).toBe('r1');
    expect(verknuepfen).toBe(true);
    expect(zusatz).toEqual({ id: 'r1' });
  });

  test('eine eigene Kennung bleibt stehen — sie kann anderswo gebraucht werden', () => {
    // Act
    const { id, verknuepfen, zusatz } = feldVerknuepfung({ id: 'eigene' }, 'r1');

    // Assert
    expect(id).toBe('eigene');
    expect(verknuepfen).toBe(true);
    expect(zusatz).toEqual({});
  });

  test('ein Feld mit eigenem Namen bekommt keinen zweiten', () => {
    // Zwei Namen, die auseinanderlaufen, sind schlimmer als einer.
    // Act
    const { verknuepfen } = feldVerknuepfung({ 'aria-label': 'Suche' }, 'r1');

    // Assert
    expect(verknuepfen).toBe(false);
  });

  test('auch aria-labelledby zählt als Name', () => {
    expect(feldVerknuepfung({ 'aria-labelledby': 'x' }, 'r1').verknuepfen).toBe(false);
  });

  test('ohne erzeugte Kennung wird nichts verknüpft statt falsch verknüpft', () => {
    // Act
    const { verknuepfen } = feldVerknuepfung({}, '');

    // Assert
    expect(verknuepfen).toBe(false);
  });
});

describe('beschriftungsText', () => {
  test('das Pflicht-Sternchen fällt aus dem Namen, nicht vom Bildschirm', () => {
    expect(beschriftungsText('Unternehmensname *')).toBe('Unternehmensname');
  });

  test('ein Doppelpunkt ebenso', () => {
    expect(beschriftungsText('E-Mail:')).toBe('E-Mail');
  });

  test('was keine Zeichenkette ist, ergibt keinen Namen', () => {
    expect(beschriftungsText(undefined)).toBe('');
    expect(beschriftungsText(42)).toBe('');
  });
});
