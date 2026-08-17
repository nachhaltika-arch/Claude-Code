/**
 * Die Stufen des Homepage Standards — eine Quelle für das ganze Frontend.
 *
 * Die Schwellen standen doppelt im Haus: das Backend staffelte 95/85/70/50
 * (`services/audit_criteria.py::LEVELS`), Widget und Akquise-Haken staffelten
 * 85/70/50/30. Derselbe Score hiess damit im Bericht „Silber" und im Widget
 * „Gold" — ein stiller Fehler mit direkter Aussenwirkung, weil beides beim
 * selben Empfaenger ankommt.
 *
 * Die Werte hier folgen dem Backend. Aendert sich der Standard, aendert sich
 * `audit_criteria.py` zuerst und diese Datei mit.
 */

// Absteigend geprueft: die erste erreichte Schwelle gilt.
export const STUFEN = [
  { ab: 95, name: 'Homepage Standard Platin', zeichen: '💎' },
  { ab: 85, name: 'Homepage Standard Gold',   zeichen: '🥇' },
  { ab: 70, name: 'Homepage Standard Silber', zeichen: '🥈' },
  { ab: 50, name: 'Homepage Standard Bronze', zeichen: '🥉' },
  { ab: 0,  name: 'Nicht konform',            zeichen: '⚠️' },
];

/** Die Stufe zu einem Score — ohne Zeichen, wie sie das Backend schreibt. */
export function stufeFuerScore(score) {
  const punkte = Number(score) || 0;
  return STUFEN.find(s => punkte >= s.ab).name;
}

/**
 * Die Stufe fuer die Anzeige, mit Zeichen.
 *
 * Liegt die Stufe vom Server vor, gilt sie — nur sie kennt die K.-o.-Regeln,
 * die eine Seite unabhaengig vom Score deckeln (kein Impressum, kein TLS).
 * Nachgerechnet wird nur, wenn nichts geliefert wurde.
 */
export function stufeAnzeige(score, stufeVomServer = '') {
  const name = (stufeVomServer || '').trim() || stufeFuerScore(score);
  const treffer = STUFEN.find(s => s.name === name);
  return treffer ? `${name} ${treffer.zeichen}` : name;
}


/**
 * Die Stufe in einem Wort — fuer enge Stellen wie die Betriebsliste.
 *
 * Dort stand am Score nur ein farbiger Balken, und welche Schwelle welche
 * Farbe bedeutet, stand nirgends: Die Stufe hing allein im `title`, also im
 * Tooltip. Ein Tooltip ist keine Beschriftung — auf einem Berührungsgeraet
 * gibt es ihn gar nicht (UX-28).
 *
 * @param {number|string} score
 * @param {string} [stufeVomServer]
 * @returns {string} „Platin", „Gold", „Silber", „Bronze" oder „Nicht konform"
 */
export function stufeKurz(score, stufeVomServer = '') {
  const voll = (stufeVomServer || stufeFuerScore(score)).trim();
  return voll.replace(/^Homepage Standard\s+/, '');
}
