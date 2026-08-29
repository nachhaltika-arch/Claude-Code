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

function seiten() {
  return seitenEinsammeln(SEITEN).map((datei) => {
    const text = ohneZeichenketten(fs.readFileSync(datei, 'utf8'));
    const stufen = [...text.matchAll(/<h([1-6])[\s>]/g)].map((m) => Number(m[1]));
    return {
      name: path.relative(SEITEN, datei).split(path.sep).join('/'),
      stufen,
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
      hatTitelBaustein: text.includes('<SeitenTitel>')
        || text.includes('<Rechtstext'),
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
      if (vorher && stufe > vorher + 1) {
        springer.push(`${seite.name}: h${vorher} → h${stufe}`);
        break;
      }
      vorher = stufe;
    }
  }

  expect(springer).toEqual([]);
});
