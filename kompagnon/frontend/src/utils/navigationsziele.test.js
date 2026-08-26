/**
 * Jedes `navigate(...)` muss auf eine Adresse zeigen, die es gibt.
 *
 * **Der Anlass (26.08.2026).** Beim Anschliessen des `AlertBanner` (L-95)
 * schrieb ich `navigate('/app/projekte/' + id)`. Die Route heisst
 * `/app/projects/:id`. Nichts waere abgestuerzt: Die Auffangroute schickt
 * alles Unbekannte zur Anmeldung, und der Innendienst haette gesehen, wie
 * ihn ein Klick auf eine Warnung abmeldet.
 *
 * **Das ist die Form von L-64**, nur andersherum. Dort fehlten die Routen zu
 * vorhandenen Seiten, hier zeigte ein vorhandener Knopf auf eine Route, die
 * es nicht gibt. Beide Male: kein Fehler, kein roter Test, keine Meldung —
 * nur eine Anmeldeseite, wo etwas anderes stehen sollte.
 *
 * **Drei Fallen, alle beim Bauen hineingetappt und deshalb hier notiert:**
 *
 * 1. *Die Auffangroute zaehlt nicht.* `path="*"` passt auf alles; zaehlte sie
 *    mit, traefe jeder Tippfehler eine Route. Die erste Gegenprobe blieb
 *    genau deshalb gruen.
 * 2. *Routen sind verschachtelt.* `<Route path="/app">` enthaelt `dashboard`,
 *    und darin liegt `settings` mit `notifications`. Flach ausgelesen ergibt
 *    das achtzig Fehltreffer.
 * 3. *`[^>]*>` findet das Ende eines Tags nicht.* In `element={() => …}`
 *    steht ein `>`. Genau dieser Ausdruck hat bei den Feldnamen schon einmal
 *    ein Tag zerschnitten (L-17, „Methodisch") — und mich hier ein zweites
 *    Mal: Der Stapel schloss nie, und die Pfade wuchsen zu Ungetuemen von
 *    tausend Zeichen. Es wird gezaehlt, nicht gemustert.
 */
const fs = require('fs');
const path = require('path');

const QUELLE = path.join(__dirname, '..');

/**
 * Ziele, die es absichtlich nicht als Route gibt. Jedes ist nachgesehen.
 */
const GEDULDET = new Set([
  // `/` hat **keine** Route; die Auffangroute schickt dorthin Navigierende
  // zur Anmeldung. Fuer ein Innendienst-Werkzeug ist das vertretbar — fuer
  // `CheckoutSuccess` weniger, dort landet ein Mensch nach bezahlter
  // Rechnung auf der Anmeldeseite. Am 26.08.2026 als Befund notiert; ob `/`
  // eine eigene Seite bekommt, ist eine Produktentscheidung, kein Versehen,
  // das dieser Test beheben sollte.
  '/',
]);

function dateien(ordner = QUELLE, gesammelt = []) {
  for (const eintrag of fs.readdirSync(ordner, { withFileTypes: true })) {
    const voll = path.join(ordner, eintrag.name);
    if (eintrag.isDirectory()) dateien(voll, gesammelt);
    else if (/\.jsx?$/.test(eintrag.name) && !/\.test\.jsx?$/.test(eintrag.name)) {
      gesammelt.push(voll);
    }
  }
  return gesammelt;
}

/**
 * Das Ende des Tags, das bei `start` beginnt — unter Mitzaehlen von
 * geschweiften Klammern und Anfuehrungszeichen.
 */
function tagEnde(text, start) {
  let tiefe = 0;
  let anfuehrung = null;
  for (let i = start; i < text.length; i++) {
    const z = text[i];
    if (anfuehrung) {
      if (z === anfuehrung) anfuehrung = null;
      continue;
    }
    if (z === '"' || z === "'" || z === '`') anfuehrung = z;
    else if (z === '{') tiefe++;
    else if (z === '}') tiefe--;
    else if (z === '>' && tiefe === 0) return i;
  }
  return -1;
}

/** Alle deklarierten Routen als vollstaendige Pfade. */
function alleRouten() {
  const app = fs.readFileSync(path.join(QUELLE, 'App.jsx'), 'utf8');
  const stapel = [];
  const gesammelt = [];

  for (let i = 0; i < app.length; i++) {
    if (app.startsWith('</Route>', i)) {
      stapel.pop();
      i += 7;
      continue;
    }
    if (!app.startsWith('<Route', i)) continue;

    const ende = tagEnde(app, i);
    if (ende === -1) break;
    const tag = app.slice(i, ende + 1);
    const treffer = /path="([^"]*)"/.exec(tag);
    const eltern = stapel.length ? stapel[stapel.length - 1] : '';

    let voll = eltern;
    if (treffer) {
      voll = treffer[1].startsWith('/')
        ? treffer[1]
        : `${eltern.replace(/\/$/, '')}/${treffer[1]}`;
      gesammelt.push(voll);
    }
    if (!tag.endsWith('/>')) stapel.push(voll);
    i = ende;
  }
  return gesammelt;
}

function routenMuster() {
  return alleRouten()
    // Nur die **Auffangroute** faellt weg, nicht jede mit Stern. `akademie/*`
    // ist eine echte Umleitung (`AkademieUmleitung`) und ein gueltiges Ziel;
    // haette ich sie mit weggeworfen, meldete der Waechter vier Stellen als
    // kaputt, die es nicht sind. Ein Waechter mit Fehltreffern wird
    // abgeschaltet — deshalb steht hier die genaue Bedingung.
    .filter((route) => route !== '*' && route !== '/*')
    .map((route) => {
      const roh = route
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/:[A-Za-z_][A-Za-z0-9_]*/g, '[^/]+')
        .replace(/\\?\*/g, '.*');
      return new RegExp(`^${roh}$`);
    });
}

function ziele() {
  const gefunden = [];
  for (const datei of dateien()) {
    const text = fs.readFileSync(datei, 'utf8');
    // Nur absolute Ziele. Relative (`navigate(-1)`, `navigate(ziel)`) sind
    // von hier aus nicht zu beurteilen und gehoeren nicht in diese Pruefung.
    for (const m of text.matchAll(/navigate\(\s*[`'"](\/[^`'"?#]*)/g)) {
      gefunden.push({
        datei: path.relative(QUELLE, datei),
        zeile: text.slice(0, m.index).split('\n').length,
        ziel: m[1],
      });
    }
  }
  return gefunden;
}

test('der Routenbaum wird richtig gelesen', () => {
  // Die Bedingung, unter der die Prüfung darunter überhaupt etwas aussagt.
  // Beide Stockwerke müssen dabei sein, und die Pfade dürfen sich nicht
  // aneinanderhängen — genau das tat der erste Entwurf.
  const routen = alleRouten();

  expect(routen).toContain('/app/dashboard');
  expect(routen).toContain('/app/settings/notifications');
  expect(routen.every((r) => r.length < 120)).toBe(true);
});

test('jedes Navigationsziel trifft eine deklarierte Route', () => {
  // Arrange
  const muster = routenMuster();

  // Act
  const insLeere = ziele().filter(({ ziel }) => {
    const form = ziel.replace(/\$\{[^}]*\}/g, 'X').replace(/(.)\/$/, '$1');
    return !GEDULDET.has(form) && !muster.some((m) => m.test(form));
  });

  // Assert
  expect(insLeere.map((z) => `${z.datei}:${z.zeile} → ${z.ziel}`)).toEqual([]);
});

test('die Prüfung liest überhaupt etwas', () => {
  // Ein Wächter, der nichts findet, weil sein Ausdruck nicht mehr passt, ist
  // grün und wertlos. Die Zahlen sind die vom Tag der Einführung.
  expect(routenMuster().length).toBeGreaterThanOrEqual(60);
  expect(ziele().length).toBeGreaterThanOrEqual(60);
});
