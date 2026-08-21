/**
 * L-17, dritte Klasse: 167 Elemente, die nur die Maus erreicht.
 *
 * WCAG 2.1.1 ist Stufe A — ein Ausfall heißt nicht „schlechter bedienbar",
 * sondern „gar nicht bedienbar".
 */
import { aufTaste } from './tastaturBedienung';

const ereignis = (key) => ({ key, preventDefault: jest.fn() });

describe('aufTaste', () => {
  test('Enter löst aus', () => {
    // Arrange
    const handler = jest.fn();

    // Act
    aufTaste(handler)(ereignis('Enter'));

    // Assert
    expect(handler).toHaveBeenCalledTimes(1);
  });

  test('die Leertaste löst aus', () => {
    const handler = jest.fn();
    aufTaste(handler)(ereignis(' '));
    expect(handler).toHaveBeenCalledTimes(1);
  });

  test('die Leertaste scrollt dabei nicht die Seite weg', () => {
    // Arrange
    const e = ereignis(' ');

    // Act
    aufTaste(jest.fn())(e);

    // Assert
    expect(e.preventDefault).toHaveBeenCalled();
  });

  test('jede andere Taste tut nichts', () => {
    // Sonst löst Tabulieren aus, was man gerade nur ansteuern wollte.
    const handler = jest.fn();
    for (const key of ['Tab', 'a', 'Escape', 'ArrowDown', 'Shift']) {
      aufTaste(handler)(ereignis(key));
    }
    expect(handler).not.toHaveBeenCalled();
  });

  test('das Ereignis wird durchgereicht', () => {
    // Handler rufen darauf `stopPropagation` — verschluckt man es, klickt
    // der Nutzer die Karte darunter mit.
    const handler = jest.fn();
    const e = ereignis('Enter');
    aufTaste(handler)(e);
    expect(handler).toHaveBeenCalledWith(e);
  });

  test('ohne Handler fällt nichts um', () => {
    expect(() => aufTaste(undefined)(ereignis('Enter'))).not.toThrow();
  });
});
