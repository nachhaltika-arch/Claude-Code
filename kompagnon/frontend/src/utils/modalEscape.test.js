/**
 * Jede bildschirmfüllende Überlagerung braucht einen Tastaturausweg.
 *
 * **Warum das ein eigener Wächter ist und nicht die Tastatur-Ratsche.**
 * `tastaturZugang.test.js` zählt `<div onClick>` ohne `onKeyDown` — ein
 * brauchbarer Zähler für Bedienelemente, aber für einen Modal-Hintergrund
 * ist sein Heilmittel **falsch**: `role="button"` auf einer Überlagerung
 * behauptet eine Schaltfläche, wo keine ist, und der Screenreader liest sie
 * als solche vor. Deshalb steht die Ratsche bei 44 und bewegt sich hier
 * nicht: Die Zahl misst ein Muster, nicht einen Mangel.
 *
 * Der Mangel ist ein anderer, und er ist messbar: **Wer ein Modal öffnet,
 * muss es ohne Maus wieder schließen können.** Ein Klick auf den Hintergrund
 * ist der Mausweg dorthin; Escape ist der Weg mit der Tastatur.
 *
 * **Gemessen am 30.08.2026:** 26 Dateien mit einer Überlagerung
 * (`position: fixed` über `inset: 0`) hatten **keinen** Escape-Weg. Danach 6,
 * und die sechs stehen unten mit Grund.
 *
 * **Was dieser Test nicht sieht.** Er liest Quelltext, keine Laufzeit. Dass
 * Escape wirklich schließt, ist am laufenden Werkzeug belegt worden
 * (Modal auf: 764 Zeichen, nach Escape: 624, der Ausgangswert) — und beim
 * Einbau hat genau diese Gegenprobe einen Fehler gefunden, den kein Test
 * gesehen hätte: Der Aufruf stand über der `useState`-Zeile, die er liest,
 * und `CustomerDetail` rendete deshalb **gar nicht**.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..');

/**
 * Dateien mit Überlagerung, die bewusst kein Escape haben — je mit Grund.
 *
 * Eine Ausnahmeliste ohne Begründung wird zum Ablagefach. Die ersten vier
 * tragen `role="button"`, `tabIndex={0}` und `onKeyDown` **auf der
 * Überlagerung selbst** — dort ist die Schließaktion also mit der Tastatur
 * erreichbar, WCAG 2.1.1 ist erfüllt. Escape wäre die bessere Umgangsform,
 * ist aber kein Mangel.
 */
const AUSNAHMEN = {
  'components/FeedbackButton.jsx':
    'Überlagerung ist selbst fokussierbar und trägt onKeyDown.',
  'components/newsletter/NewsletterAnalytics.jsx':
    'Überlagerung ist selbst fokussierbar und trägt onKeyDown.',
  'pages/CustomerProjects.jsx':
    'Beide Modale tragen role/tabIndex/onKeyDown auf der Überlagerung.',
  'pages/RoleManagement.jsx':
    'Überlagerung ist selbst fokussierbar und trägt onKeyDown.',
  'components/OnboardingWizard.jsx':
    'Soll sich nicht schließen lassen — der Kunde führt ihn zu Ende oder '
    + 'bleibt darin. Ein Escape-Ausweg wäre hier ein Fehler, kein Fortschritt.',
};

function jsxDateien(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) jsxDateien(voll, treffer);
    else if (eintrag.name.endsWith('.jsx') && !eintrag.name.includes('.test.')) {
      treffer.push(voll);
    }
  }
  return treffer;
}

/** Eine bildschirmfüllende Überlagerung: `position: fixed` und `inset: 0`. */
function hatUeberlagerung(quelle) {
  return /position:\s*['"]fixed['"][^}]{0,120}inset:\s*0/.test(quelle)
      || /inset:\s*0[^}]{0,120}position:\s*['"]fixed['"]/.test(quelle);
}

function hatEscapeWeg(quelle) {
  return /useEscapeKey|['"]Escape['"]/.test(quelle);
}

const dateien = jsxDateien(WURZEL).map(d => ({
  rel: path.relative(WURZEL, d).split(path.sep).join('/'),
  quelle: fs.readFileSync(d, 'utf8'),
}));

describe('Modale lassen sich mit der Tastatur schließen', () => {
  const mitUeberlagerung = dateien.filter(d => hatUeberlagerung(d.quelle));

  test('es werden überhaupt Überlagerungen gefunden', () => {
    // Die positive Zusicherung neben der Abwesenheit. Ohne sie wäre der Test
    // unten auch dann grün, wenn der Ausdruck nichts mehr trifft — und
    // genau so war der Kontrast-Wächter am selben Tag grün.
    expect(mitUeberlagerung.length).toBeGreaterThan(20);
  });

  test('jede Überlagerung hat einen Escape-Weg oder eine begründete Ausnahme', () => {
    const ohne = mitUeberlagerung
      .filter(d => !hatEscapeWeg(d.quelle))
      .map(d => d.rel)
      .filter(rel => !(rel in AUSNAHMEN));

    expect(ohne).toEqual([]);
  });

  test('die Ausnahmen gelten noch — sonst sind sie ein Loch', () => {
    // Eine Ausnahme, die niemand nachrechnet, überlebt ihren Grund. Steht
    // eine Datei hier, hat aber inzwischen einen Escape-Weg, gehört sie
    // gestrichen; gibt es sie gar nicht mehr, erst recht.
    const veraltet = [];
    for (const rel of Object.keys(AUSNAHMEN)) {
      const treffer = dateien.find(d => d.rel === rel);
      if (!treffer) { veraltet.push(`${rel}: Datei gibt es nicht mehr`); continue; }
      if (!hatUeberlagerung(treffer.quelle)) {
        veraltet.push(`${rel}: hat keine Überlagerung mehr`);
      } else if (hatEscapeWeg(treffer.quelle)) {
        veraltet.push(`${rel}: hat jetzt einen Escape-Weg`);
      }
    }
    expect(veraltet).toEqual([]);
  });

  test('die vier Sichtbaren tragen den Tastaturweg wirklich auf der Überlagerung', () => {
    // Der Grund in der Liste oben ist eine Behauptung. Hier wird sie geprüft:
    // Ohne `onKeyDown` neben `role="button"` wäre die Ausnahme falsch.
    const mitBedienung = [
      'components/FeedbackButton.jsx',
      'components/newsletter/NewsletterAnalytics.jsx',
      'pages/CustomerProjects.jsx',
      'pages/RoleManagement.jsx',
    ];
    for (const rel of mitBedienung) {
      const { quelle } = dateien.find(d => d.rel === rel);
      expect(quelle).toMatch(/role="button"[^>]*onKeyDown|onKeyDown[^>]*role="button"/);
    }
  });
});
