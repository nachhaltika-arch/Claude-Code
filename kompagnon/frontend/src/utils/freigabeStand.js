/**
 * Wie die Spalte `content_freigaben` zu lesen ist.
 *
 * **Warum eine eigene Datei.** Zwei Stellen lasen dieselbe Spalte nach zwei
 * verschiedenen Regeln, und am 22.08.2026 waren beide falsch:
 *
 *   `ProzessFlow.jsx`         `.some(v => v === true)`
 *   `customer/Freigaben.jsx`  `v.status === 'ausstehend'`
 *
 * Das Backend schreibt seit dem Umbau weder das eine noch das andere, sondern
 * `{status: "freigegeben"|"abgelehnt"|"angefragt", …}`. Beide Leseorte waren
 * auf einem Stand stehengeblieben, den es nicht mehr gibt — dieselbe Bauart
 * wie der Fund in `schrittkette.js`: eine Entscheidung, die einen ganzen
 * Ablauf sperren kann, inline in einer Datei, die kein Test laden kann.
 *
 * Was sie anrichteten:
 *
 *   ProzessFlow    Ein Objekt ist nie `=== true`. Der Schritt
 *                  „Content-Freigabe" konnte nie fertig werden, und der
 *                  Ablauf sprang beim Öffnen immer wieder dorthin zurück,
 *                  obwohl die Freigabe vorlag.
 *   Freigaben.jsx  Eine offene Anfrage („angefragt") galt als entschieden
 *                  und verschwand aus genau der Liste, die der Kunde
 *                  abarbeiten soll.
 *
 * **Altdatensätze bleiben gültig.** Einträge, die noch `true` oder
 * `"ausstehend"` tragen, werden weiter richtig gelesen. Es gibt keine
 * Migration, die sie umschreibt, und es soll auch keine geben: Die
 * Schreibweise eines Datensatzes ist kein Grund, ihn anzufassen.
 */

/** Die beiden Endzustände. Alles andere ist offen — auch Unbekanntes. */
export const ENTSCHIEDENE_ZUSTAENDE = ['freigegeben', 'abgelehnt'];

/**
 * Nimmt die Spalte, wie sie ankommt: als Text, als Objekt oder gar nicht.
 * Die Spalte ist mal `TEXT`, mal `JSONB` — je nachdem, welcher Endpunkt sie
 * geliefert hat. Ein leeres Ergebnis ist kein Fehler, sondern „noch nichts".
 */
function leseFreigaben(roh) {
  if (!roh) return {};
  try {
    const gelesen = typeof roh === 'string' ? JSON.parse(roh) : roh;
    return gelesen && typeof gelesen === 'object' ? gelesen : {};
  } catch {
    return {};
  }
}

/**
 * Ist ein einzelner Eintrag entschieden — freigegeben oder abgelehnt?
 *
 * `true` aus der Altzeit zählt als freigegeben, weil es damals genau das
 * bedeutete.
 */
export function istEntschieden(eintrag) {
  if (eintrag === true) return true;
  if (!eintrag || typeof eintrag !== 'object') return false;
  return ENTSCHIEDENE_ZUSTAENDE.includes(eintrag.status);
}

/** Ist ein einzelner Eintrag freigegeben? Eine Ablehnung ist es nicht. */
function istFreigegeben(eintrag) {
  if (eintrag === true) return true;
  if (!eintrag || typeof eintrag !== 'object') return false;
  return eintrag.status === 'freigegeben';
}

/**
 * Gilt der Schritt „Content-Freigabe" als erledigt?
 *
 * Bewusst `some` und nicht `every`: **eine** freigegebene Seite genügt. Das
 * war die Regel vorher und bleibt es. Ob fachlich alle angefragten Seiten
 * nötig sein sollten, ist eine eigene Frage — ein Formatfehler und eine
 * fachliche Änderung gehören nicht in denselben Schritt, sonst weiß hinterher
 * niemand, was gewirkt hat.
 */
export function istContentFreigegeben(roh) {
  const werte = Object.values(leseFreigaben(roh));
  return werte.length > 0 && werte.some(istFreigegeben);
}
