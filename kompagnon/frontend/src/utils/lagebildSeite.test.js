/**
 * Das Lagebild muss sich auch **öffnen** lassen (10.09.2026).
 *
 * **Der Anlass.** Am 07.09. kam der Produktkatalog in die Vorlage. Der Block
 * ruft `schutz()` auf, deklariert war das als `const` weiter unten — beim
 * Laden warf die Seite deshalb „Cannot access 'schutz' before
 * initialization", und zwar an der **ersten** Verwendung. Alles danach lief
 * nie: Modulkarte, Lückenliste, Abarbeitungsplan, Meilensteine. Sichtbar
 * blieben nur die Kennzahlen im Kopf.
 *
 * **Drei Tage fiel das niemandem auf**, und der Grund ist die eigentliche
 * Lehre: Der Erzeuger schreibt beim Bauen „194 Lücken: 34 offen …" auf die
 * Standleiste, und diese Zahlen stimmten weiter. Sie entstehen im Skript,
 * nicht auf der Seite. Wer nur die Ausgabe liest, sieht ein gesundes
 * Lagebild — dieselbe Klasse wie ein Wächter, der seinen eigenen Kommentar
 * mitzählt: Gemessen wurde das Werkzeug, nicht der Gegenstand.
 *
 * Dieser Test lädt die **erzeugte Datei** und lässt ihre Skripte laufen.
 */
import fs from 'fs';
import path from 'path';
import { JSDOM } from 'jsdom';

const DATEI = path.join(
  __dirname, '..', '..', '..', '..', 'docs', 'lagebild', 'kompagnon-lagebild.html',
);

let dom;
let fehler;

beforeAll(() => {
  fehler = [];
  const html = fs.readFileSync(DATEI, 'utf8');
  const virtualConsole = new (require('jsdom').VirtualConsole)();
  virtualConsole.on('jsdomError', (e) => fehler.push(String(e.message)));
  dom = new JSDOM(html, { runScripts: 'dangerously', virtualConsole });
});

afterAll(() => { if (dom) dom.window.close(); });

describe('Das erzeugte Lagebild', () => {
  test('läuft ohne Ausnahme durch', () => {
    // Die positive Probe steht unten; ohne diese hier wüsste man nur, dass
    // etwas leer ist, nicht warum.
    expect(fehler).toEqual([]);
  });

  test.each([
    ['liste', 'die Lückenliste'],
    ['module', 'die Modulkarte'],
    ['produkte', 'der Produktkatalog'],
    ['phasen', 'der Abarbeitungsplan'],
  ])('%s ist gefüllt (%s)', (id) => {
    const el = dom.window.document.getElementById(id);
    expect(el).not.toBeNull();
    expect(el.children.length).toBeGreaterThan(0);
  });

  test('es stehen tatsächlich Lücken-Karten darin', () => {
    // `#liste` hätte auch bei „Kein Punkt passt zu dieser Auswahl" ein Kind.
    const karten = dom.window.document.querySelectorAll('details.luecke');
    expect(karten.length).toBeGreaterThan(0);
  });

  test('die Datei nennt ihren Zeichensatz', () => {
    // Ohne <meta charset> las die Seite als Latin-1, sobald der Server den
    // Zeichensatz nicht selbst mitschickt — „PrioritÃ¤t" statt „Priorität".
    const meta = dom.window.document.querySelector('meta[charset]');
    expect(meta).not.toBeNull();
    expect(meta.getAttribute('charset').toLowerCase()).toBe('utf-8');
  });
});
