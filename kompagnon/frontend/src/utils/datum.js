/**
 * Datumsangaben fuer die Anzeige — an einer Stelle.
 *
 * Anlass war ein sichtbares **„Invalid Date"** in der Betriebsansicht
 * (`LeadProfile.jsx`, Kachel „Letzter Audit"). Beim Nachsehen war es kein
 * Einzelfall: Rund vierzig Stellen formatieren Datumswerte, und sie tun es auf
 * zwei Arten falsch.
 *
 * **Erstens ungeprueft.** `new Date(undefined).toLocaleDateString('de-DE')`
 * ergibt die Zeichenkette „Invalid Date" — sie sieht aus wie ein Wert und wird
 * ohne Weiteres in die Oberflaeche gedruckt.
 *
 * **Zweitens halb geprueft.** Der uebliche Schutz `x ? new Date(x)… : '—'`
 * faengt nur das Fehlen. Ein Wert, der da ist, aber nicht lesbar
 * (`'0000-00-00'`, ein abgeschnittener Zeitstempel, ein Freitext aus einem
 * Import), ist wahr und faellt trotzdem durch — mit demselben „Invalid Date".
 *
 * Beides faengt dieser Helfer: Was sich nicht in ein Datum verwandeln laesst,
 * bekommt den Ersatztext. **Nie „Invalid Date", nie eine erfundene Zeit.**
 */

/** Steht, wo ein Datum fehlt. Kurz, weil es meist in Tabellenzellen steht. */
export const KEIN_DATUM = '—';

/**
 * Wandelt eine Eingabe in ein gueltiges `Date` — oder in `null`.
 *
 * Zahlen sind Zeitstempel in Millisekunden. Ein `Date` wird durchgereicht,
 * wenn es gueltig ist. Alles andere geht durch `new Date(...)` und muss dabei
 * eine lesbare Zeit ergeben.
 */
export function alsDatum(wert) {
  if (wert === null || wert === undefined || wert === '') return null;

  const datum = wert instanceof Date ? wert : new Date(wert);
  return Number.isNaN(datum.getTime()) ? null : datum;
}

/** Ob sich aus dem Wert ein Datum lesen laesst. */
export function istDatum(wert) {
  return alsDatum(wert) !== null;
}

function formatiere(wert, optionen, ersatz) {
  const datum = alsDatum(wert);
  if (!datum) return ersatz;
  return datum.toLocaleDateString('de-DE', optionen);
}

/** `17.08.2026` */
export function datumKurz(wert, ersatz = KEIN_DATUM) {
  return formatiere(wert, { day: '2-digit', month: '2-digit', year: 'numeric' }, ersatz);
}

/** `17. August 2026` */
export function datumLang(wert, ersatz = KEIN_DATUM) {
  return formatiere(wert, { day: 'numeric', month: 'long', year: 'numeric' }, ersatz);
}

/** `August 2026` — fuer Verlaeufe ueber Monate. */
export function monatUndJahr(wert, ersatz = KEIN_DATUM) {
  return formatiere(wert, { month: 'long', year: 'numeric' }, ersatz);
}

/** `17.08.2026, 14:32` */
export function datumUndZeit(wert, ersatz = KEIN_DATUM) {
  const datum = alsDatum(wert);
  if (!datum) return ersatz;
  return datum.toLocaleString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/** `14:32` — fuer Verlaeufe innerhalb eines Tages. */
export function nurZeit(wert, ersatz = KEIN_DATUM) {
  const datum = alsDatum(wert);
  if (!datum) return ersatz;
  return datum.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}
