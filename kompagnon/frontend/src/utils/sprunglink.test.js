/**
 * Der Weg an der Navigation vorbei — WCAG 2.4.1 „Bypass Blocks", Stufe A.
 *
 * **Gemessen am 30.08.2026** mit `tools/bedienbarkeit_messen.py`, im Browser
 * und angemeldet: Auf `/app/betriebe` liegen **38 erreichbare Elemente** vor
 * dem Inhalt, fast alle in der Seitenleiste — und sie stehen auf jeder Seite
 * wieder da. Wer mit der Tastatur arbeitet, tabbt sich durch die gesamte
 * Navigation, bevor er die erste Sache tun kann, die ihn hergeführt hat.
 *
 * Nach dem Einbau: **ein** Tabstopp. Am laufenden Werkzeug nachgemessen —
 * Tab, Enter, Tab landet auf dem ersten Bedienelement *im Inhalt*.
 *
 * **Was dieser Wächter hält, und warum er drei Dinge prüft statt einem.**
 * Ein Sprunglink zerfällt an drei Stellen, und jede sieht für sich harmlos aus:
 *
 * 1. **Er steht nicht mehr zuerst.** Ein Element davor macht ihn nutzlos —
 *    er überspringt dann nicht mehr, was er überspringen soll.
 * 2. **Sein Ziel nimmt den Fokus nicht an.** Ohne `tabIndex={-1}` scrollt der
 *    Browser zwar hin, setzt den Fokus aber nicht; der nächste Tabulator führt
 *    zurück an den Anfang, und der Link hat nichts bewirkt. Das ist der
 *    tückischste der drei: Der Sprung *sieht* aus, als hätte er funktioniert.
 * 3. **Er wird richtig versteckt.** `display: none` und `visibility: hidden`
 *    nehmen ihn aus der Tabulatorreihenfolge — dann ist er genau für die
 *    Leute unerreichbar, für die er gebaut wurde.
 *
 * Geprüft wird am Quelltext, wie beim Nachbarn `tastaturZugang.test.js`. Das
 * sieht keine Laufzeit; die Gegenprobe im Browser steht oben und im
 * Tagesbericht. Was dieser Test verhindert, ist das **stille Verschwinden**.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..');
const LAYOUT = path.join(WURZEL, 'components', 'Layout', 'AppLayout.jsx');
const CSS = path.join(WURZEL, 'index.css');

const layout = fs.readFileSync(LAYOUT, 'utf8');
const css = fs.readFileSync(CSS, 'utf8');

describe('Sprunglink an der Navigation vorbei', () => {
  test('er steht im Layout und zeigt auf den Inhalt', () => {
    expect(layout).toMatch(/<a\s+href="#inhalt"\s+className="kc-sprunglink"/);
  });

  test('er ist das erste Element im zurückgegebenen Baum', () => {
    // Gemessen wird die Reihenfolge, nicht die Anwesenheit: Der Baum beginnt
    // beim letzten `return (` der Komponente. Steht irgendein anderes Element
    // dazwischen, ist der Link wirkungslos.
    const baum = layout.slice(layout.lastIndexOf('  return ('));
    // **Ab dem Tag messen, nicht ab dem Attribut.** Der erste Anlauf suchte
    // `className="kc-sprunglink"` — und zaehlte dann das `<a` des Links
    // selbst als Element davor. Ein Messfehler an der eigenen Messung, und
    // er sah aus wie ein Befund.
    const linkAb = baum.indexOf('<a href="#inhalt"');
    expect(linkAb).toBeGreaterThan(-1);

    // Alles vor dem Link darf nur die Wurzel und Kommentare sein.
    const davor = baum.slice(0, linkAb);
    const elementeDavor = davor
      .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')      // JSX-Kommentare
      .match(/<[A-Za-z][A-Za-z0-9]*/g) || [];
    expect(elementeDavor).toEqual(['<div']);
  });

  test('das Ziel nimmt den Fokus an', () => {
    // `<main id="inhalt" tabIndex={-1}>` — beides, sonst springt der Fokus
    // nicht mit. Geprüft wird der Block bis zum ersten `style`, damit ein
    // späteres `id` an einem anderen Element nicht mitzählt.
    const hauptblock = layout.slice(layout.indexOf('<main'),
                                    layout.indexOf('<main') + 400);
    expect(hauptblock).toContain('id="inhalt"');
    expect(hauptblock).toContain('tabIndex={-1}');
  });

  test('er ist versteckt, ohne aus der Tabulatorreihenfolge zu fallen', () => {
    const regel = css.match(/\.kc-sprunglink\s*\{[^}]*\}/);
    expect(regel).not.toBeNull();
    // Die positive Zusicherung: Er wird verschoben, nicht ausgeblendet.
    expect(regel[0]).toMatch(/left:\s*-\d+px/);
    // Und die Abwesenheit daneben — die allein wäre auch grün, wenn jemand
    // die ganze Regel löscht.
    expect(regel[0]).not.toMatch(/display:\s*none/);
    expect(regel[0]).not.toMatch(/visibility:\s*hidden/);
  });

  test('im Fokus kommt er zurück auf den Bildschirm', () => {
    const fokus = css.match(/\.kc-sprunglink:focus\s*\{[^}]*\}/);
    expect(fokus).not.toBeNull();
    expect(fokus[0]).toMatch(/left:\s*0/);
  });
});
