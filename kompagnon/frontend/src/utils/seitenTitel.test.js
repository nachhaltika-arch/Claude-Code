/**
 * L-17, zweite Hälfte: die Überschriftenhierarchie.
 *
 * Gemessen am 21.08.2026: 27 von 66 Seiten ohne jedes `<h1>`, 13 davon ganz
 * ohne Überschrift. Ein Screenreader-Nutzer springt über Überschriften — auf
 * diesen Seiten gab es nichts, wohin.
 *
 * **Zwei eigene Fehlmessungen, beide beim Nachprüfen gefunden:**
 *
 * 1. Die erste Zählung sah `<SeitenTitel>` nicht als `<h1>` — der Baustein
 *    erzeugt eines, im Quelltext der Seite steht aber keines. 22 gerade
 *    reparierte Seiten galten dadurch weiter als kaputt.
 * 2. `TemplateLibrary.jsx` wurde mit **neun** `<h1>` gemeldet. Acht davon
 *    stehen in HTML-Vorlagen für **Kundenseiten**, also in Zeichenketten —
 *    sie gehören nicht zum Werkzeug. Genauso `AuditTool.jsx`: Seine drei
 *    `<h1>` liegen in drei Zweigen, von denen immer nur einer gerendert wird.
 *
 * Dieser Wächter zählt deshalb ohne Zeichenketten und kennt beide Bausteine.
 */
const fs = require('fs');
const path = require('path');

const SEITEN = path.join(__dirname, '..', 'pages');

/** Vorlagen für Kundenseiten stehen in Backticks — ihre Überschriften sind
 *  nicht die des Werkzeugs. */
function ohneZeichenketten(text) {
  return text
    .replace(/`(?:[^`\\]|\\[\s\S])*`/g, '``')
    .replace(/'(?:[^'\\\n]|\\.)*'/g, "''")
    .replace(/"(?:[^"\\\n]|\\.)*"/g, '""');
}

function seitenEinsammeln(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) seitenEinsammeln(voll, treffer);
    else if (/\.jsx?$/.test(eintrag.name) && !eintrag.name.includes('.test.')) treffer.push(voll);
  }
  return treffer;
}

const WURZEL = path.join(__dirname, '..');

/**
 * Der Quelltext einer Seite **samt der Bausteine, die sie einbindet**.
 *
 * **Warum das am 30.08.2026 dazukam.** `LeadProfile` ist geteilt worden
 * (L-25): Der Reiter „Übersicht" liegt seither in
 * `components/betriebsblatt/ReiterUebersicht.jsx` — und mit ihm das `h2`,
 * das zwischen dem `h1` der Seite und den `h3` der Abschnitte steht. Dieser
 * Test meldete daraufhin `h1 → h3`.
 *
 * **Er hatte recht über die Datei und unrecht über die Seite.** Gerendert
 * steht die Folge unverändert da; nur liest sie sich nicht mehr aus einer
 * Datei ab. Eine Überschriftenhierarchie ist eine Eigenschaft der
 * **Seite**, nicht der Datei — also folgt die Prüfung jetzt den Importen,
 * eine Ebene tief. Tiefer nicht: Zwei Ebenen brächten Bausteine mit, die auf
 * anderen Seiten anders eingebettet sind, und dann misst man wieder etwas
 * anderes als das Gemeinte.
 */
function mitBausteinen(datei, text) {
  const roh = fs.readFileSync(datei, 'utf8');
  const teile = [text];
  for (const m of roh.matchAll(/from '(\.\.?\/[^']+)'/g)) {
    const ziel = path.resolve(path.dirname(datei), m[1]);
    for (const endung of ['.jsx', '.js', '/index.jsx', '/index.js']) {
      if (!fs.existsSync(ziel + endung)) continue;
      // Nur Bausteine aus dem eigenen Baum, keine Bibliotheken.
      if (!(ziel + endung).startsWith(WURZEL)) break;
      teile.push(ohneZeichenketten(fs.readFileSync(ziel + endung, 'utf8')));
      break;
    }
  }
  return teile.join('\n');
}

function seiten() {
  return seitenEinsammeln(SEITEN).map((datei) => {
    const text = ohneZeichenketten(fs.readFileSync(datei, 'utf8'));
    const volltext = mitBausteinen(datei, text);
    // **Die Reihenfolge kommt aus der Seite, die Verfuegbarkeit aus den
    // Bausteinen.** Aneinandergehaengte Dateien haben keine Renderreihenfolge
    // — der erste Anlauf am 30.08.2026 las die Stufen aus dem Volltext und
    // meldete daraufhin drei Seiten als Springer, darunter eine ungeteilte.
    // Was ein Baustein beitraegt, ist deshalb kein Platz in der Folge,
    // sondern nur die Antwort auf „gibt es diese Stufe ueberhaupt".
    const stufen = [...text.matchAll(/<h([1-6])[\s>]/g)].map((m) => Number(m[1]));
    const ausBausteinen = new Set(
      [...volltext.matchAll(/<h([1-6])[\s>]/g)].map((m) => Number(m[1])),
    );
    return {
      name: path.relative(SEITEN, datei).split(path.sep).join('/'),
      stufen,
      ausBausteinen,
      // Beide Bausteine erzeugen ein h1 — im Quelltext der Seite steht keines.
      // `<PageHeader` stand hier als zweite erlaubte Form. Die Komponente
      // war laut L-17 von **null** Seiten benutzt und ist am 26.08.2026
      // entfernt; eine Alternative, die es nicht gibt, macht die Pruefung
      // nur unschaerfer.
      // `<Rechtstext` kam am 29.08.2026 dazu (ORDERS_05): AGB und
      // Widerrufsbelehrung teilen sich eine Huelle, die das h1 und das
      // Warnband fuer ausstehende Texte traegt. Zwei Kopien derselben
      // Darstellung driften auseinander, und die dritte Rechtsseite
      // vergisst das Band — dieselbe Ueberlegung wie bei `Feld.jsx`.
      hatTitelBaustein: volltext.includes('<SeitenTitel>')
        || volltext.includes('<Rechtstext'),
    };
  });
}

/**
 * Seiten ohne eigene Darstellung. Jede ist nachgesehen.
 */
const GEPRUEFTE_AUSNAHMEN = [
  // Eine reine Weiche: Sie gibt entweder eine der drei Paketseiten zurück —
  // die tragen ihre eigene Überschrift — oder leitet zur Kasse um. Eigenes
  // Markup hat sie keines.
  'PaketSeite.jsx',
];

test('jede Seite hat genau eine Hauptüberschrift', () => {
  const ohne = seiten()
    .filter((s) => !GEPRUEFTE_AUSNAHMEN.includes(s.name))
    .filter((s) => !s.hatTitelBaustein && !s.stufen.includes(1))
    .map((s) => s.name);

  expect(ohne).toEqual([]);
});

test('keine Seite überspringt eine Überschriftenstufe', () => {
  // h1 → h3 heißt für einen Screenreader: hier fehlt ein Abschnitt.
  const springer = [];
  for (const seite of seiten()) {
    const stufen = seite.hatTitelBaustein ? [1, ...seite.stufen] : seite.stufen;
    let vorher = 0;
    for (const stufe of stufen) {
      // Eine uebersprungene Stufe ist nur dann ein Befund, wenn sie **auch
      // in keinem eingebundenen Baustein** vorkommt: Seit dem 30.08.2026
      // liegen Reiter in eigenen Dateien (L-25), und das `h2` steht dort.
      const fehlt = [];
      for (let n = vorher + 1; n < stufe; n += 1) {
        if (!seite.ausBausteinen.has(n)) fehlt.push(n);
      }
      if (vorher && fehlt.length) {
        springer.push(`${seite.name}: h${vorher} → h${stufe}`);
        break;
      }
      vorher = stufe;
    }
  }

  expect(springer).toEqual([]);
});
