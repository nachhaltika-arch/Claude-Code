/**
 * Der Baustein, der die Beschriftung an ihr Feld bindet — gerendert geprüft.
 *
 * Anlass ist ein roter CI-Lauf: Die erste Fassung benutzte `Children.only`
 * und warf, sobald eine Hülle mehr als ein Kind bekam. In
 * `ComponentLibrary.jsx` ist das der Normalfall — ein `<select>` und darunter
 * eine Knopfreihe. Die Seite stürzte ab, vier Browser-Tests fielen um, und
 * die Unit-Tests hatten nichts davon gesehen: Sie prüften die Entscheidung
 * (`feldBeschriftung.js`), nicht das Rendern.
 *
 * Siehe [[feedback-am-gegenstand-pruefen]] — der Gegenstand ist hier die
 * gerenderte Ausgabe, nicht die Hilfsfunktion daneben.
 */
import { renderToStaticMarkup } from 'react-dom/server';

import Feld from './Feld';

const zeichne = (element) => renderToStaticMarkup(element);

describe('Feld', () => {
  test('verknüpft Beschriftung und Feld über htmlFor', () => {
    // Act
    const markup = zeichne(
      <Feld label="Kategorie">
        <select><option>A</option></select>
      </Feld>,
    );

    // Assert — dieselbe Kennung auf beiden Seiten
    const fuer = /<label[^>]*for="([^"]+)"/.exec(markup);
    const id = /<select[^>]*id="([^"]+)"/.exec(markup);
    expect(fuer).not.toBeNull();
    expect(id).not.toBeNull();
    expect(fuer[1]).toBe(id[1]);
  });

  test('mehrere Kinder stürzen nicht ab — das war der rote CI-Lauf', () => {
    // Act
    const markup = zeichne(
      <Feld label="Layout-Preset">
        <select><option>Beliebig</option></select>
        <div>Knopfreihe</div>
      </Feld>,
    );

    // Assert
    expect(markup).toContain('Knopfreihe');
    expect(/<label[^>]*for="/.test(markup)).toBe(true);
  });

  test('ohne Formularelement wird nichts verknüpft statt falsch verknüpft', () => {
    // htmlFor auf ein <div> ist ungültig — dann lieber keine Verknüpfung.
    // Act
    const markup = zeichne(
      <Feld label="Slots">
        <div><input aria-label="Slot 1" /></div>
      </Feld>,
    );

    // Assert
    expect(/<label[^>]*for="/.test(markup)).toBe(false);
    expect(markup).toContain('aria-label="Slot 1"');
  });

  test('ein Feld mit eigenem Namen behält ihn', () => {
    // Act
    const markup = zeichne(
      <Feld label="Slug"><input aria-label="Slug" /></Feld>,
    );

    // Assert — kein zweiter Name, keine Verknüpfung, die ihn übersteuert
    expect(markup).toContain('aria-label="Slug"');
    expect(/<label[^>]*for="/.test(markup)).toBe(false);
  });

  test('eine eigene Kennung des Feldes bleibt stehen', () => {
    // Act
    const markup = zeichne(
      <Feld label="Name"><input id="meine-id" /></Feld>,
    );

    // Assert
    expect(markup).toContain('id="meine-id"');
    expect(markup).toContain('for="meine-id"');
  });

  test('das Pflicht-Sternchen steht sichtbar da, aber nicht im Namen', () => {
    // Act
    const markup = zeichne(
      <Feld label="Titel *"><input /></Feld>,
    );

    // Assert
    expect(markup).toContain('aria-hidden="true"');
    expect(markup).toContain('Titel');
  });
});
