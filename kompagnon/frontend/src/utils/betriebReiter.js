// Welche Reiter der Betriebsansicht oben stehen und welche darunter.
//
// Zehn gleichrangige Reiter waren zehn Entscheidungen bei jedem Aufruf
// (UX-15). Sechs stehen jetzt oben — die, die im Tagesgeschäft gebraucht
// werden —, vier liegen hinter „Mehr". Nichts ist weg; es ist nur nicht mehr
// alles gleich laut.
//
// Entschieden von David am 17.08.2026. Diese Datei hält die Entscheidung an
// einer Stelle fest, statt sie über das Markup zu verteilen.

/** Oben, in dieser Reihenfolge. */
export const HAUPT_REITER = [
  'overview',   // der Einstieg
  'contact',    // Stammdaten, wird beim Bearbeiten angesteuert
  'audits',     // der Kern des Angebots
  'offer',      // daraus entsteht das Geschäft
  'messages',   // trägt den Ungelesen-Zähler, muss sichtbar bleiben
  'dateien',    // Anhänge des Betriebs
];

/** Hinter „Mehr". */
export const MEHR_REITER = [
  'deals',      // steht auch unter Vertrieb → Deals
  'akademy',    // kundenseitig, nicht Innendienst
  'qrcode',     // Zugang, einmal je Betrieb gebraucht
  'emails',     // Verlauf; gehört sachlich zu Nachrichten
];

/** Liegt dieser Reiter hinter „Mehr"? */
export function istImMehr(reiterId) {
  return MEHR_REITER.includes(reiterId);
}

/**
 * Teilt die Reiterliste auf und sagt, ob „Mehr" hervorzuheben ist.
 *
 * Die Reihenfolge kommt aus `HAUPT_REITER`, nicht aus der Eingabe — sonst
 * entscheidet die alte Anordnung weiter mit.
 *
 * @param {Array<{id: string}>} reiter
 * @param {string} aktiv
 */
export function aufteilung(reiter = [], aktiv = '') {
  const nach = (ids) => ids
    .map(id => reiter.find(r => r.id === id))
    .filter(Boolean);

  return {
    haupt: nach(HAUPT_REITER),
    mehr: nach(MEHR_REITER),
    mehrIstAktiv: istImMehr(aktiv),
  };
}
