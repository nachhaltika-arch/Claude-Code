/**
 * Jeder Menüpunkt führt irgendwohin.
 *
 * **Der Befund (27.08.2026, gemeldet von David).** Unter „Verwaltung" stand
 * der Eintrag „Rollen" mit dem Pfad `/app/admin/roles`. Diesen Pfad gibt es
 * nicht — die Rollenverwaltung liegt unter `/app/settings/roles`. Wer darauf
 * klickte, landete im Auffang, und der schickte bis zum selben Tag jeden
 * unbekannten Pfad auf die **Anmeldemaske**. David hielt sich für
 * abgemeldet.
 *
 * Das ist zweimal dieselbe Fehlerklasse an einem Punkt: ein Knopf, der ins
 * Leere führt (L-64), und ein Weg, der still bei der Anmeldung endet.
 *
 * **Warum ein Wächter und nicht nur die Korrektur.** Menü und Routen stehen
 * in zwei Dateien, und niemand merkt es, wenn eine sich bewegt. Genau so ist
 * dieser Eintrag entstanden: `AdminUsers` liegt tatsächlich unter
 * `/app/admin/users`, und die Rollenverwaltung sah aus, als läge sie daneben.
 *
 * **Was hier gemessen wird und was nicht.** Geprüft wird, ob zu jedem
 * Menüpfad eine Route existiert — nicht, ob die Seite dahinter etwas
 * anzeigt. Das eine ist eine Zusicherung, das andere wäre eine Behauptung.
 */
const fs = require('fs');
const path = require('path');
const { ohneKommentare } = require('./ohneKommentare');

const QUELLE = path.join(__dirname, '..');

function lies(datei) {
  return ohneKommentare(fs.readFileSync(path.join(QUELLE, datei), 'utf8'));
}

/** Alle Pfade aus dem Menü. */
function menuePfade() {
  const text = lies('utils/menue.js');
  return [...text.matchAll(/path:\s*'(\/app\/[^']+)'/g)].map((m) => m[1]);
}

/**
 * Alle erreichbaren Adressen aus `App.jsx`.
 *
 * **Bewusst einfach — und die Annahme steht hier.** Ein erster Anlauf
 * verfolgte die Verschachtelung mit einem Stapel und meldete dreissig Pfade
 * als fehlend, die es alle gibt: `<Route path="audit">` liegt unter
 * `<Route path="/app">`, und die Klammerung ueber mehrere Zeilen mit einem
 * Muster nachzubauen ging schief. Ein Waechter, der dreissig Fehlalarme
 * erzeugt, wird abgeschaltet und nicht repariert.
 *
 * Deshalb der schlichtere Weg: Jeder gefundene `path`-Wert wird als
 * **Kandidat** unter den beiden Elternpfaden gefuehrt, die es in dieser
 * Datei gibt — `/app` und `/app/settings`. Das ist keine Nachbildung des
 * Routers, und es soll auch keine sein: Es beantwortet genau die Frage
 * „gibt es dazu ueberhaupt eine Route".
 *
 * **Was das kostet:** Eine Route `x` unter `/app/settings` wuerde auch
 * `/app/x` gutschreiben. Der Waechter meldet dadurch eher zu wenig als zu
 * viel — und das ist die richtige Richtung fuer einen Test, der bei jedem
 * Lauf laeuft. Er faengt den Fall, um den es ging: einen Pfad, den es
 * **nirgends** gibt.
 */
const ELTERN = ['/app', '/app/settings'];

function routen() {
  const text = lies('App.jsx');
  const gefunden = new Set();
  for (const treffer of text.matchAll(/<Route\s+path="([^"]+)"/g)) {
    const teil = treffer[1];
    if (teil === '*') continue;
    if (teil.startsWith('/')) {
      gefunden.add(teil);
      continue;
    }
    for (const eltern of ELTERN) gefunden.add(`${eltern}/${teil}`);
  }
  return gefunden;
}


/** Trifft eine Route diesen Pfad? Platzhalter wie `:id` zaehlen mit. */
function passt(route, pfad) {
  if (route === pfad) return true;
  const muster = new RegExp(
    `^${route.replace(/:[^/]+/g, '[^/]+').replace(/\//g, '\\/')}$`
  );
  return muster.test(pfad);
}

test('jeder Menüpunkt führt zu einer Route, die es gibt', () => {
  // Arrange
  const alleRouten = routen();
  const pfade = menuePfade();

  // Act
  const ohneZiel = pfade.filter((p) => ![...alleRouten].some((r) => passt(r, p)));

  // Assert
  expect(ohneZiel).toEqual([]);
});

test('das Menü ist nicht leer und die Routen sind es auch nicht', () => {
  // **Die Gegenprobe.** Ohne sie wäre der Test oben auch dann grün, wenn
  // eines von beidem nicht gelesen werden könnte — und ein Wächter, der
  // nichts findet, sieht aus wie einer, der nichts zu beanstanden hat.
  expect(menuePfade().length).toBeGreaterThan(20);
  expect(routen().size).toBeGreaterThan(50);
});
