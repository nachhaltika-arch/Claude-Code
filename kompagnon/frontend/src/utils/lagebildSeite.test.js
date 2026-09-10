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

/**
 * **Kein `var(--…)` ohne Definition** (10.09.2026).
 *
 * Beim Einbau des Reiters „Messtiefe" habe ich drei Token benutzt, die es
 * nicht gibt: `--kc-gelb` (heisst `--kc-yellow`), `--flaeche` (heisst
 * `--senke`) und `--mono` (war nirgends definiert). Beim Nachzählen kamen
 * vier weitere aus früheren Ergänzungen dazu — `--haengt`, `--traegt`,
 * `--mid`, `--linie-2`.
 *
 * **Warum das niemandem auffiel:** Ein unbekanntes Token macht die
 * Eigenschaft ungültig, nicht die Seite. Bei `color` erbt sie einfach; bei
 * einer `font`-Kurzform fällt die ganze Regel weg. Nichts bricht, nichts
 * meldet sich — es sieht nur anders aus, als es soll. Zwei Kennzahlen
 * standen dunkelblau auf dunklem Grund und waren im Dunkelschema unlesbar.
 *
 * Geprüft wird die **erzeugte Datei**, nicht die Vorlage: ausgeliefert wird
 * sie.
 */
/**
 * **Nur die Stilblöcke.** Der erste Anlauf durchsuchte die ganze Datei und
 * schlug bei `var(--text)` an — das stand in der **Beschreibung** einer
 * Lücke, die Quelltext zitiert. Ein Wächter, der Fliesstext für CSS hält,
 * meldet Fehler, die keine sind, und wird nach dem zweiten Mal abgeschaltet.
 */
function stilbloecke(html) {
  return [...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)]
    .map((m) => m[1])
    .join('\n');
}

describe('Farbtoken', () => {
  test('jedes benutzte Token ist auch definiert', () => {
    const css = stilbloecke(fs.readFileSync(DATEI, 'utf8'));
    const definiert = new Set(
      [...css.matchAll(/(--[a-z0-9-]+)\s*:/g)].map((m) => m[1]),
    );
    const benutzt = new Set(
      [...css.matchAll(/var\((--[a-z0-9-]+)\)/g)].map((m) => m[1]),
    );
    const fehlend = [...benutzt].filter((t) => !definiert.has(t));
    expect(fehlend).toEqual([]);
    // Positiv daneben: Der Test darf nicht deshalb grün sein, weil er
    // nichts gefunden hat.
    expect(benutzt.size).toBeGreaterThan(15);
  });

  test('keine Textfarbe hängt an einem Token ohne Dunkelfassung', () => {
    /* `--kc-dark` ist die Markenfarbe und bleibt im Dunkelschema dunkel —
       richtig so. Genau deshalb darf sie dort nicht als **Textfarbe**
       stehen: dunkles Blau auf dunklem Grund ist unlesbar. Zwei Kennzahlen
       im Reiter „Messtiefe" waren es. */
    const css = stilbloecke(fs.readFileSync(DATEI, 'utf8'));
    // Die Schreibweise wechselt (mit und ohne Leerzeichen) — deshalb ein
    // Muster und keine feste Zeichenkette. Beim ersten Anlauf suchte der
    // Test nach der Fassung mit Leerzeichen und fand die ohne nicht.
    const schnitt = css.search(/prefers-color-scheme\s*:\s*dark/);
    expect(schnitt).toBeGreaterThan(0);
    const hell = css.slice(0, schnitt);
    const dunkel = css.slice(schnitt);
    const nurHell = [...hell.matchAll(/(--[a-z0-9-]+)\s*:/g)]
      .map((m) => m[1])
      .filter((t) => !dunkel.includes(`${t}:`));
    const suender = nurHell.filter((t) =>
      new RegExp(`color:\\s*var\\(${t}\\)`).test(hell),
    );
    expect(suender).toEqual([]);
  });
});
