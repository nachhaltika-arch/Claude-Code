/**
 * Der Kanalbericht aus L-84, aufbereitet für die Anzeige.
 *
 * `GET /api/leads/quellen/wirkung` liefert je Herkunft Betriebe, Kunden und
 * Quote — **sortiert**, und diese Reihenfolge bleibt hier unangetastet: Der
 * Server sortiert nach Wirkung und bei gleicher Quote nach Bestand; ein
 * zweites Sortieren im Browser wäre eine zweite Wahrheit.
 *
 * Aufbereitet wird nur, was die Anzeige sonst falsch machen würde: eine Quote,
 * die es nicht gibt, und die Betriebe ohne Herkunft, die kein Kanal ist.
 */

/**
 * Anteil (0–1) als Prozentangabe.
 *
 * **`null` ist nicht `0`.** Ein Kanal ohne Betriebe hat keine Quote; „0 %"
 * behauptete, er wirke nicht — gemessen wurde aber gar nichts.
 *
 * @param {number|null|undefined} quote
 * @returns {string}
 */
export function quoteText(quote) {
  if (typeof quote !== 'number' || Number.isNaN(quote)) return '—';
  return `${Math.round(quote * 100)} %`;
}

/** Eine Zahl, oder 0 — aber nie `NaN` in der Anzeige. */
function zahl(wert) {
  return typeof wert === 'number' && Number.isFinite(wert) ? wert : 0;
}

/**
 * @param {object|null} antwort Die Antwort von `/api/leads/quellen/wirkung`.
 * @returns {{kanaele: object[], ohneHerkunft: number, summeKanaele: number,
 *            gesamt: number}}
 */
export function kanaeleAufbereiten(antwort) {
  const kanaele = Array.isArray(antwort?.kanaele) ? antwort.kanaele : [];
  return {
    kanaele,
    ohneHerkunft: zahl(antwort?.ohne_herkunft),
    // **Beide Zahlen, nicht eine.** Die Summe der Kanäle ist nicht der
    // Gesamtbestand — dazwischen liegen die Betriebe ohne Herkunft. Wer nur
    // eine davon zeigt, lädt zum Fehlschluss ein.
    summeKanaele: kanaele.reduce((summe, k) => summe + zahl(k.betriebe), 0),
    gesamt: zahl(antwort?.betriebe_gesamt),
  };
}
