/**
 * L-17, zweite Klasse: Formularfelder ohne programmatisch lesbaren Namen.
 *
 * Gemessen am 21.08.2026: **399 Formularsteuerelemente**, davon **18** mit
 * einem Namen. 209 `<label>`-Elemente standen im Quellbaum — sichtbar war
 * fast alles beschriftet, verknüpft fast nichts. Das ist WCAG 1.3.1/4.1.2
 * und damit genau das, was wir bei Kunden prüfen.
 *
 * **Eine Korrektur an der eigenen Messung:** 23 der angeblich namenlosen
 * Felder stehen *innerhalb* eines `<label>` und sind damit implizit
 * verknüpft — auch ohne `htmlFor`. Die richtige Zahl war 358, nicht 381.
 *
 * Dieser Wächter zählt nicht die einzelnen Stellen, sondern hält die Regel:
 * Ein Formularfeld hat einen Namen. Er prüft am Quelltext, weil es kein
 * Renderwerkzeug im Projekt gibt (`@testing-library` ist nicht installiert)
 * — was er dadurch nicht sehen kann, steht unten als Ausnahme benannt.
 */
const fs = require('fs');
const path = require('path');

const WURZEL = path.join(__dirname, '..');

/** Das `>`, das ein Tag wirklich schließt — `onChange={e => f(e)}` enthält
 *  eines, das keines ist. Ein Muster wie `[^>]*>` schneidet dort falsch. */
function tagEnde(text, start) {
  let tiefe = 0;
  let anfuehrung = null;
  for (let i = start; i < text.length; i += 1) {
    const z = text[i];
    if (anfuehrung) {
      if (z === anfuehrung) anfuehrung = null;
    } else if (z === '"' || z === "'" || z === '`') {
      anfuehrung = z;
    } else if (z === '{') {
      tiefe += 1;
    } else if (z === '}') {
      tiefe -= 1;
    } else if (z === '>' && tiefe === 0) {
      return i;
    }
  }
  return -1;
}

function dateienEinsammeln(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) dateienEinsammeln(voll, treffer);
    else if (/\.jsx?$/.test(eintrag.name) && !eintrag.name.includes('.test.')) treffer.push(voll);
  }
  return treffer;
}

const AUSGENOMMEN = /type\s*=\s*["'{]?\s*(hidden|submit|button)/i;
const HAT_NAMEN = /aria-label(ledby)?\s*=/;

/**
 * Stellen, an denen der Name erst zur Laufzeit entsteht und ein Blick in den
 * Quelltext ihn deshalb nicht sehen kann. Jede ist nachgesehen worden.
 */
const GEPRUEFTE_AUSNAHMEN = [
  // Eigene `Select`-Bausteine, die eine `id` als Eigenschaft bekommen; das
  // umgebende `Field` verknüpft sie über `htmlFor` (beide Wizards machen es
  // seit jeher richtig — von dort stammen 10 der ursprünglich 18 Namen).
  'components/BriefingWizard.jsx',
  'components/LeistungsseitenWizard.jsx',
  // `function Input(props) { return <input {...props} …/> }` — reicht alle
  // Eigenschaften durch, also auch den Namen, den der Aufrufer setzt.
  'pages/AuditTool.jsx',
];

function unbenannteFelder() {
  const fund = [];
  for (const datei of dateienEinsammeln(WURZEL)) {
    const relativ = path.relative(WURZEL, datei).split(path.sep).join('/');
    if (GEPRUEFTE_AUSNAHMEN.includes(relativ)) continue;

    const text = fs.readFileSync(datei, 'utf8');
    const verknuepfteIds = new Set([...text.matchAll(/htmlFor=["']([^"']+)["']/g)].map((m) => m[1]));

    const muster = /<(input|select|textarea)\b/g;
    let treffer = muster.exec(text);
    while (treffer !== null) {
      const anfang = treffer.index;
      const ende = tagEnde(text, muster.lastIndex);
      if (ende !== -1) {
        const attrs = text.slice(muster.lastIndex, ende);
        const eigeneId = /\bid=["']([^"']+)["']/.exec(attrs);
        const davor = text.slice(0, anfang);
        const umschlossen = davor.lastIndexOf('<label') > davor.lastIndexOf('</label>');
        const inHuelle = Math.max(davor.lastIndexOf('<Field '), davor.lastIndexOf('<Feld '), davor.lastIndexOf('<F '))
          > Math.max(davor.lastIndexOf('</Field>'), davor.lastIndexOf('</Feld>'), davor.lastIndexOf('</F>'));

        const benannt = HAT_NAMEN.test(attrs)
          || (eigeneId && verknuepfteIds.has(eigeneId[1]))
          || umschlossen
          || inHuelle;

        if (!AUSGENOMMEN.test(attrs) && !benannt) {
          fund.push(`${relativ}:${davor.split('\n').length} <${treffer[1]}>`);
        }
      }
      treffer = muster.exec(text);
    }
  }
  return fund;
}

test('jedes Formularfeld hat einen Namen, den ein Screenreader vorlesen kann', () => {
  // Ein Feld ohne Namen wird als „Eingabefeld" angesagt — der Nutzer weiß
  // nicht, was hineingehört. Ein Werkzeug, das BFSG-Konformität verkauft und
  // 95 % namenlose Felder hat, ist schwer zu verteidigen.
  expect(unbenannteFelder()).toEqual([]);
});
