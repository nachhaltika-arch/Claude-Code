/**
 * Jede Farbe, die als Text benutzt wird, muss auf ihrem Grund lesbar sein (L-17).
 *
 * **Der Unterschied zu `tokenKontrast.test.js`.** Der prüft, ob die *als
 * Kommentar notierten* Kontrastzahlen stimmen. Tokens ohne Kommentar prüft er
 * nicht — und genau dort lag der Fehler.
 *
 * **Der Fund vom 28.08.2026.** `--brand-primary-mid` stand im dunklen
 * Tokensatz auf `#2a5a6a`. Als **Textfarbe** auf `--surface` sind das **2.18**;
 * die Schwelle für normalen Text ist 4.5. Das Token wird an **78 Stellen** als
 * `color:` gesetzt — im Dunkelmodus war dieser Text unlesbar, und niemandem
 * war es aufgefallen, weil keine Zahl danebenstand. Jetzt `#3f9fb2` (5.37).
 *
 * **Drei eigene Fehlmessungen beim Bauen dieses Tests, alle in dieselbe
 * Richtung — und deshalb steht die Lehre hier und nicht nur im Verlauf:**
 *
 * 1. Erst wurde *jedes* Text-Token gegen *jede* Fläche gerechnet. Das meldete
 *    zwölf Verstöße, von denen keiner einer war: `--text-inverse` und
 *    `--text-on-brand` gehören nicht auf `--surface`, sie sind für dunklen
 *    beziehungsweise markenfarbenen Grund gemacht.
 * 2. Dann wurde `--text-on-brand` gegen `--brand-primary-mid` gerechnet — auch
 *    falsch: Dieses Token ist keine Fläche, es ist eine Schriftfarbe.
 * 3. `--brand-primary-light` fiel mit 1.43 durch und wird **nirgends** als
 *    Text benutzt (0 Vorkommen, 35 als Hintergrund).
 *
 * Ein Kontrasttest, der Paare prüft, die es nicht gibt, ist ein
 * Fehlalarm-Erzeuger — und wird abgeschaltet. Deshalb steht hier eine
 * **ausdrückliche Paarliste** statt eines Kreuzprodukts.
 *
 * **Und deshalb prüft der letzte Test die Ausnahmen nach.** Eine Ausnahmeliste,
 * die niemand nachrechnet, verwandelt sich in ein Loch: Sobald jemand
 * `--brand-primary-light` doch als Schriftfarbe verwendet, gilt hier weiter
 * „wird nicht als Text benutzt" — und die Prüfung schweigt zu genau dem Fall,
 * für den sie gebaut wurde.
 */
import fs from 'fs';
import path from 'path';

import { AA_TEXT, kontrast } from './kontrast';

const WURZEL = path.join(__dirname, '..');
const TOKENS = path.join(WURZEL, 'styles', 'tokens.css');

/** Welche Schriftfarbe ist für welchen Grund gemacht. */
const PAARE = [
  ['--text', '--surface'],
  ['--text', '--paper'],
  ['--text', '--bg-active'],
  ['--text-60', '--surface'],
  ['--text-60', '--paper'],
  ['--text-60', '--bg-active'],
  ['--text-45', '--surface'],
  ['--text-45', '--paper'],
  ['--brand-primary-mid', '--surface'],
  ['--brand-primary-mid', '--paper'],
  // Am 30.08.2026 dazugekommen (L-17). Der Token heisst „text" und wird als
  // Linkfarbe benutzt (Fehlerprotokoll, Portal-Anmeldung) — er stand
  // trotzdem nicht in dieser Liste und war deshalb nie geprueft. Mit
  // #008EAA erreichte er 3.69.
  ['--text-brand', '--surface'],
  ['--text-brand', '--paper'],
  // Am 31.08.2026 dazugekommen (L-17) — und wieder aus demselben Grund wie
  // `--text-brand` einen Tag zuvor: Die vier Statusfarben werden als
  // Schriftfarbe benutzt und standen trotzdem nicht in dieser Liste.
  //
  // Anlass war die Browsermessung: acht Zeichen unter AA, und es waren
  // **Ziffern** — `{score}/{cat.max}` im Kundendashboard, gefaerbt von
  // derselben Funktion, die auch den Balken daneben faerbt. Der Balken darf
  // kraeftig sein, die Ziffern muessen lesbar sein; seither sind es zwei
  // Funktionen.
  //
  // Die Token selbst waren immer in Ordnung (4,69 bis 9,12 in beiden Modi).
  // Falsch war, dass die Oberflaeche sie an 89 Stellen gar nicht benutzt hat,
  // sondern feste Hex-Werte — und ein fester Wert kann sich im Dunkelmodus
  // nicht umstellen.
  ['--success', '--surface'],
  ['--success', '--paper'],
  ['--warn', '--surface'],
  ['--warn', '--paper'],
  ['--error', '--surface'],
  ['--error', '--paper'],
  ['--info', '--surface'],
  ['--info', '--paper'],
  // Am 06.09.2026 dazugekommen (L-176). `--brand-primary` ist die Farbe, auf
  // die zwölf Stellen von `--kc-dark` umgestellt wurden — sie *muss* geprüft
  // sein, sonst hätte die Reparatur denselben blinden Fleck wie der Fehler.
  // 8,38 hell / 8,02 dunkel. `--brand-primary-dark` stand ebenfalls in keiner
  // der beiden Listen und wird an mehreren Stellen als Schrift benutzt.
  ['--brand-primary', '--surface'],
  ['--brand-primary', '--paper'],
  ['--brand-primary-dark', '--surface'],
  ['--brand-primary-dark', '--paper'],
];

/**
 * Als Schrift benutzt, **fällt durch** — mit Nummer im Lagebild.
 *
 * **Warum eine dritte Kategorie und nicht eine Ausnahme.** Eine Ausnahme sagt
 * „das ist in Ordnung so". Diese vier sind es nicht: Sie sind der Rest des
 * Befunds L-176, den derselbe Wächter zutage gefördert hat, als er zum ersten
 * Mal lief. Sie hier als Ausnahme einzutragen hieße, einen Mangel als
 * Entscheidung zu tarnen — und genau das ist die Bauart, die dieses Projekt
 * schon mehrfach Zeit gekostet hat.
 *
 * Der Test unten verlangt für jeden Eintrag eine L-Nummer. Ist die Lücke
 * geschlossen, verschwindet der Eintrag hier — und wenn ihn jemand vergisst,
 * meldet ihn der nächste Systemdurchlauf erneut.
 */
const BEFUNDE_OFFEN = [
  { token: '--kc-black', luecke: 'L-180',
    befund: 'Dunkelmodus 1,27 auf --surface — dieselbe Klasse wie --kc-dark: '
      + 'eine Palettenfarbe, die als Schrift gesetzt wird.' },
  { token: '--kc-mid', luecke: 'L-180',
    befund: 'Hellmodus 3,48 auf --surface, Schwelle 4,5. Im Dunkelsatz ist '
      + 'sie mit 8,02 richtig — der Mangel steht nur im hellen Satz.' },
  { token: '--border-medium', luecke: 'L-180',
    befund: 'Eine Rahmenfarbe als Schrift (Trennzeichen, Platzhaltertext). '
      + 'rgba auf wechselndem Grund; der Wert ist nicht einmal ausrechenbar.' },
  { token: '--kc-success', luecke: 'L-180',
    befund: 'Das Token gibt es in tokens.css **nicht**. Benutzt wird es mit '
      + 'Rückfall #1D9E75 im Analyse-Widget — also greift immer der feste '
      + 'Wert, und im Dunkelmodus bleibt die Farbe stehen.' },
];

/**
 * Absichtlich nicht geprüft — mit Grund, und der Grund wird nachgerechnet.
 * `pruefeUngenutzt` heisst: Das Token darf im Quellbaum nicht als `color:`
 * auftauchen; tut es das doch, ist die Ausnahme hinfällig.
 */
const AUSNAHMEN = [
  { token: '--text-30', pruefeUngenutzt: false,
    grund: 'Absichtlich schwach — abgeschaltete Bedienelemente, von WCAG 1.4.3 ausgenommen.' },
  { token: '--text-placeholder', pruefeUngenutzt: false,
    grund: 'Platzhalter, kein Inhalt. Der Feldname steht seit dem 21.08. programmatisch daneben.' },
  { token: '--brand-primary-light', pruefeUngenutzt: true,
    grund: 'Ist eine Fläche, keine Schriftfarbe — 35 Vorkommen als Hintergrund, null als Text.' },
  { token: '--brand-primary-deeper', pruefeUngenutzt: true,
    grund: 'Ebenfalls Fläche; als Text käme sie auf 3.97 und wäre ein Befund.' },
  // Am 06.09.2026 dazugekommen (L-176) — und der Anlass war, dass dieses
  // Token in **keiner** der beiden Listen stand und deshalb nie geprüft
  // wurde. Es ist die rohe Palettenfarbe: `--bg-sidebar` im Hellsatz,
  // `--brand-primary` im Hellsatz, und im Dunkelsatz #003840, weil es dort
  // eine dunkle Fläche sein soll. An dreizehn Stellen stand es als `color:` —
  // im Dunkelmodus 1,17 bis 1,41, also unlesbar, darunter die Überschrift
  // „Dashboard" und die Kennzahl darunter.
  //
  // Zwölf sind auf `--brand-primary` bzw. `--info` umgestellt. Die
  // dreizehnte bleibt: der Zähler in der Seitenleiste steht auf
  // `--kc-yellow` und erreicht dort 9,99 (dunkel) und 7,24 (hell). Deshalb
  // `pruefeUngenutzt: false` — das Token *darf* als Schrift vorkommen, nur
  // eben auf Gelb.
  { token: '--kc-dark', pruefeUngenutzt: false,
    grund: 'Flächenfarbe (Sidebar, Marke). Die eine verbliebene Verwendung '
      + 'als Schrift steht auf --kc-yellow und erreicht dort 9,99 bzw. 7,24.' },
  { token: '--kc-yellow', pruefeUngenutzt: false,
    grund: 'Signalfarbe für Flächen; als Schrift nur auf dunklem Grund, wo '
      + 'sie ihre Aufgabe hat — Tool-CI: Gelb höchstens einmal je Bildschirm.' },
  { token: '--bg-surface', pruefeUngenutzt: false,
    grund: 'Umgekehrte Schrift: helle Fläche als Textfarbe auf farbigem Grund '
      + '(Knopf mit Markenfüllung). Ihr Gegenstück ist der Grund, nicht --surface.' },
  { token: '--bg-app', pruefeUngenutzt: false,
    grund: 'Wie --bg-surface — umgekehrte Schrift auf farbigem Grund.' },
];

/** Zeilennummern der Blockanfänge — wie in `tokenKontrast.test.js`. */
function bloecke(zeilen) {
  const anfaenge = [];
  zeilen.forEach((zeile, i) => {
    if (/^(:root|@media|\[data-theme)/.test(zeile)) anfaenge.push({ i, kopf: zeile.trim() });
  });
  return anfaenge.map((a, n) => ({
    kopf: a.kopf,
    von: a.i,
    bis: (anfaenge[n + 1] || { i: zeilen.length }).i,
  }));
}

/**
 * Alle Deklarationen eines Blocks — **Hexwerte und Verweise**.
 *
 * **Der Fund vom 30.08.2026 (L-17).** Hier stand ein Ausdruck, der nur
 * `--name: #rrggbb;` erkannte. In `:root` ist aber fast jedes Markentoken ein
 * **Verweis**: `--brand-primary-mid: var(--kc-mid);`. Solche Zeilen fielen
 * durch — und `werteIm` gab sie nicht zurück. Die Schleife darunter
 * überspringt jedes Paar, dessen Token fehlt, „weil es erbt".
 *
 * Ergebnis: Der helle Modus wurde für diese Paare **gar nicht geprüft**, und
 * der Test war grün, weil er nichts angesehen hat. Aufgefallen ist es nicht
 * hier, sondern im Browser: `tools/bedienbarkeit_messen.py` maß
 * `rgb(0,142,170)` auf `rgb(250,250,250)` = **3.69** an der Domainzeile der
 * Betriebsliste — genau das Paar `--brand-primary-mid` auf `--paper`, das
 * oben in der Liste steht.
 *
 * Dieselbe Bauart wie die anderen wirkungslosen Wächter: Eine Prüfung, die
 * still überspringt, was sie nicht versteht, sagt „in Ordnung" und meint
 * „nicht angesehen".
 */
function werteIm(zeilen, block) {
  const roh = {};
  for (let i = block.von; i < block.bis; i += 1) {
    const treffer = zeilen[i].match(/^\s*(--[a-z0-9-]+):\s*([^;]+);/);
    if (treffer) roh[treffer[1]] = treffer[2].trim();
  }
  return roh;
}

/**
 * Einen Wert auf seine Farbe bringen — Verweise werden verfolgt.
 *
 * Zuerst im eigenen Block, dann in `:root`: Genau so löst der Browser auf,
 * und genau daran hing der Fund oben. Mehr als fünf Stufen gibt es nicht;
 * die Grenze verhindert, dass ein Ringschluss den Test hängen lässt (es gab
 * am 30.08. sechs davon in dieser Datei — siehe `tokenSelbstbezug.test.js`).
 */
function alsFarbe(wert, eigene, wurzel, tiefe = 0) {
  if (!wert || tiefe > 5) return null;
  if (/^#[0-9a-fA-F]{3,8}$/.test(wert)) return wert;
  const verweis = wert.match(/^var\((--[a-z0-9-]+)\)$/);
  if (!verweis) return null;
  const name = verweis[1];
  const naechster = eigene[name] !== undefined ? eigene[name] : wurzel[name];
  if (naechster === wert) return null;           // Selbstbezug
  return alsFarbe(naechster, eigene, wurzel, tiefe + 1);
}

const zeilen = fs.readFileSync(TOKENS, 'utf8').split('\n');
const alleBloecke = bloecke(zeilen);

describe('Kontrast der gepaarten Tokens', () => {
  const wurzelWerte = werteIm(zeilen, alleBloecke[0]);

  test.each(alleBloecke.map(b => [b.kopf, b]))('%s', (_kopf, block) => {
    const roh = werteIm(zeilen, block);
    const farbe = (name) => alsFarbe(
      roh[name] !== undefined ? roh[name] : wurzelWerte[name],
      roh, wurzelWerte,
    );
    const durchgefallen = [];

    PAARE.forEach(([schrift, grund]) => {
      // Nicht jeder Block definiert jedes Token neu — was hier fehlt, erbt
      // aus `:root`. Was sich auch dort nicht auflösen lässt, wird
      // übersprungen; der Test darunter zählt nach, dass das die Ausnahme
      // bleibt und nicht die Regel wird.
      const v = farbe(schrift);
      const h = farbe(grund);
      if (!v || !h) return;
      const wert = kontrast(v, h);
      if (wert < AA_TEXT) {
        durchgefallen.push(`${schrift} auf ${grund}: ${wert.toFixed(2)} < ${AA_TEXT}`);
      }
    });

    expect(durchgefallen).toEqual([]);
  });

  test('mindestens ein Block prüft wirklich Paare', () => {
    // Ohne das wäre der Test oben auch dann grün, wenn die Namen nicht mehr
    // passen und jedes Paar übersprungen wird.
    const geprueft = alleBloecke.map(b => {
      const roh = werteIm(zeilen, b);
      const farbe = (n) => alsFarbe(
        roh[n] !== undefined ? roh[n] : wurzelWerte[n], roh, wurzelWerte,
      );
      return PAARE.filter(([s, g]) => farbe(s) && farbe(g)).length;
    });
    // **Alle Paare, nicht „alle bis auf zwei".** Die Toleranz stammt aus der
    // Zeit, als Verweise nicht aufgelöst wurden; sie hätte am 30.08.2026
    // zugelassen, dass zwei Paare für immer ungeprüft bleiben — und genau
    // eines davon war der Befund.
    expect(Math.max(...geprueft)).toBe(PAARE.length);
  });
});

describe('Die Ausnahmen halten noch', () => {
  const quellen = [];
  (function sammle(ordner) {
    fs.readdirSync(ordner, { withFileTypes: true }).forEach(eintrag => {
      const voll = path.join(ordner, eintrag.name);
      if (eintrag.isDirectory()) {
        if (eintrag.name !== 'node_modules') sammle(voll);
      } else if (/\.(js|jsx|css)$/.test(eintrag.name) && !/\.test\./.test(eintrag.name)) {
        quellen.push(voll);
      }
    });
  })(WURZEL);

  test.each(AUSNAHMEN.filter(a => a.pruefeUngenutzt).map(a => [a.token, a]))(
    '%s wird nicht als Schriftfarbe benutzt', (token, ausnahme) => {
      const muster = new RegExp(`color:\\s*['"\`]?\\s*var\\(\\s*${token}\\b`);
      const fundstellen = quellen
        .filter(datei => muster.test(fs.readFileSync(datei, 'utf8')))
        .map(datei => path.relative(WURZEL, datei));

      expect({ token, grund: ausnahme.grund, fundstellen }).toEqual({
        token, grund: ausnahme.grund, fundstellen: [],
      });
    });

  test('jede Ausnahme trägt einen Grund', () => {
    AUSNAHMEN.forEach(a => expect(a.grund.length).toBeGreaterThan(30));
  });
});

describe('Die Liste wächst mit dem Code mit', () => {
  /**
   * **Warum dieser Test der eigentliche Fund vom 06.09.2026 ist.**
   *
   * Der Systemdurchlauf meldete `--kc-dark` mit 1,29:1 im Dunkelmodus und
   * schrieb dazu: „Warum die Token-Kontrasttests das nicht fangen: Sie rechnen
   * eine ausdrückliche Paarliste, und `--kc-dark` als Textfarbe steht darin zu
   * Recht nicht — es soll keine sein."
   *
   * Das stimmt, und es ist genau die Lücke: Die Paarliste ist **von Hand
   * gepflegt**. Ein Token, das jemand neu als `color:` einsetzt, steht weder
   * in `PAARE` noch in `AUSNAHMEN` — und wird deshalb nie geprüft. Dieselbe
   * Bauart wie bei L-51, wo ein Wächter eine handgepflegte Pfadliste prüfte,
   * während der Code weiterwuchs.
   *
   * Dieser Test dreht die Richtung um: Er liest, was **tatsächlich** als
   * Schriftfarbe benutzt wird, und verlangt für jedes Token eine Entscheidung
   * — geprüftes Paar oder begründete Ausnahme. Ein drittes gibt es nicht.
   */
  const quellen = [];
  (function sammle(ordner) {
    fs.readdirSync(ordner, { withFileTypes: true }).forEach(eintrag => {
      const voll = path.join(ordner, eintrag.name);
      if (eintrag.isDirectory()) {
        if (eintrag.name !== 'node_modules') sammle(voll);
      } else if (/\.(js|jsx|css)$/.test(eintrag.name) && !/\.test\./.test(eintrag.name)) {
        quellen.push(voll);
      }
    });
  })(WURZEL);

  const benutzt = new Set();
  quellen.forEach(datei => {
    const text = fs.readFileSync(datei, 'utf8');
    // **`color:`, nicht `*-color:`.** Der erste Wurf dieses Musters fing
    // `border-color:` und `background-color:` mit und meldete `--border-light`
    // und `--bg-surface` als angebliche Schriftfarben — vier Fehlalarme von
    // zehn Treffern. Der Suchbereich muss die Eigenschaft treffen, nicht ihre
    // Endung.
    const muster = /(?:^|[;{\s,'"`(])color\s*:\s*['"`]?\s*(?:[\w\s|?:'"`.]*?)?var\(\s*(--[a-z0-9-]+)/g;
    let treffer;
    while ((treffer = muster.exec(text)) !== null) benutzt.add(treffer[1]);
  });

  /** Farben, die als Grund dienen — sie stehen als zweiter Teil eines Paares. */
  const alsSchriftGepruef = new Set(PAARE.map(([vorne]) => vorne));
  const begruendet = new Set(AUSNAHMEN.map(a => a.token));

  test('es wird überhaupt etwas gefunden', () => {
    // Ein Wächter, der seinen Gegenstand nicht findet, ist immer grün.
    expect(benutzt.size).toBeGreaterThan(5);
  });

  test('jedes als Schrift benutzte Token ist geprüft oder begründet', () => {
    const offen = new Set(BEFUNDE_OFFEN.map(b => b.token));
    const ohne = [...benutzt]
      .filter(t => !alsSchriftGepruef.has(t) && !begruendet.has(t) && !offen.has(t))
      // `--text-*` und `--status-*` tragen ihre Rolle im Namen und werden von
      // `tokenKontrast.test.js` an ihren Kommentarzahlen geprüft.
      .filter(t => !/^--(text|status|color)-/.test(t))
      .sort();

    expect({ ungeprueft: ohne }).toEqual({ ungeprueft: [] });
  });
});

describe('Die offenen Befunde tragen eine Nummer', () => {
  test.each(BEFUNDE_OFFEN.map(b => [b.token, b]))(
    '%s verweist auf eine Lücke im Lagebild', (token, eintrag) => {
      expect(eintrag.luecke).toMatch(/^L-\d+$/);
      expect(eintrag.befund.length).toBeGreaterThan(40);
    });

  test('kein Befund steht gleichzeitig als Ausnahme', () => {
    // Sonst hätte ein Token zwei Aussagen über sich: „ist in Ordnung" und
    // „ist ein Mangel". Die zweite verlöre, weil die erste zuerst greift.
    const ausnahmen = new Set(AUSNAHMEN.map(a => a.token));
    BEFUNDE_OFFEN.forEach(b => expect(ausnahmen.has(b.token)).toBe(false));
  });
});
