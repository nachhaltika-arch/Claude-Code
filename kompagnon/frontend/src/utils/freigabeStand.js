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

/**
 * Der Stand einer einzelnen Seite im Freigaben-Reiter der Content-Werkstatt.
 *
 * **Warum es das braucht (L-79).** Der Reiter leitete den Zustand aus einer
 * Ersatzgröße ab: Wo Inhalt vorhanden war, stand „Freigabe ausstehend" — auch
 * wenn niemand je gefragt hatte. Das ist keine Kleinigkeit: Der Innendienst
 * las daraus, der Kunde sei am Zug, während der Vorgang in Wahrheit nie
 * begonnen hatte. Daneben trug der Knopf „Freigabe anfordern" **kein**
 * `onClick` — sichtbar, klickbar, folgenlos. Dieselbe Familie wie L-55.
 *
 * Vier Zustände, und `anfragbar` sagt, ob der Knopf etwas zu tun hat:
 *
 *   ohne-inhalt   Es gibt noch keinen Text — nichts vorzulegen.
 *   offen         Text da, nie angefragt. **Hier gehört der Knopf hin.**
 *   angefragt     Der Kunde ist am Zug. Erneut fragen hiesse drängeln.
 *   freigegeben   Fertig.
 *   abgelehnt     Wieder anfragbar — nach der Überarbeitung wird neu
 *                 vorgelegt, sonst endet der Ablauf in einer Sackgasse.
 */
export function standJeSeite(roh, seiteId, hatInhalt) {
  const eintrag = leseFreigaben(roh)[String(seiteId)];
  const status = eintrag === true ? 'freigegeben' : eintrag?.status;

  if (status === 'freigegeben') {
    const wann = eintrag?.freigegeben_am;
    return { zustand: 'freigegeben',
             text: wann ? `Freigegeben am ${wann}` : 'Freigegeben',
             anfragbar: false };
  }
  if (status === 'abgelehnt') {
    return { zustand: 'abgelehnt', text: 'Abgelehnt', anfragbar: true };
  }
  if (status) {
    // „angefragt" und alles, was ein Backend künftig hier ablegt: Es ist
    // etwas im Gange, also nicht noch einmal anfragen.
    const wann = eintrag?.angefragt_am;
    return { zustand: 'angefragt',
             text: wann ? `Angefragt am ${wann}` : 'Angefragt',
             anfragbar: false };
  }
  if (!hatInhalt) {
    return { zustand: 'ohne-inhalt', text: 'Content fehlt', anfragbar: false };
  }
  return { zustand: 'offen', text: 'Noch nicht angefragt', anfragbar: true };
}
