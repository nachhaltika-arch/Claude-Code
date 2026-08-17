// Die Befunde der automatischen Anreicherung, lesbar gemacht.
//
// Warum eigene Datei: Bis zum 17.08.2026 standen diese Werte als fertige
// Textzeile in `lead.notes` — im Feld fuer die Notizen eines Menschen. Sie
// liegen jetzt in eigenen Spalten, und was aus ihnen an der Oberflaeche wird,
// gehoert an eine pruefbare Stelle (UX-06).
//
// Die Regel dahinter ist die aus der UX-Pruefung: Ein unbekannter Wert wird
// weder roh gezeigt noch als etwas anderes getarnt. `null` heisst „noch nicht
// geprueft" — das ist etwas anderes als „fehlt".

/** Ab hier gilt die mobile Leistung als brauchbar. */
const PAGESPEED_BRAUCHBAR_AB = 50;

const UNBEKANNT = { wert: 'nicht geprüft', art: 'unbekannt' };

function jaNein(wert, vorhandenText = 'vorhanden', fehltText = 'fehlt') {
  if (wert === null || wert === undefined) return UNBEKANNT;
  return wert
    ? { wert: vorhandenText, art: 'gut' }
    : { wert: fehltText, art: 'fehlt' };
}

function pagespeed(wert) {
  if (wert === null || wert === undefined) return UNBEKANNT;
  return {
    wert: `${wert}/100`,
    art: wert >= PAGESPEED_BRAUCHBAR_AB ? 'gut' : 'fehlt',
  };
}

/**
 * @param {{has_ssl?: boolean|null, has_impressum?: boolean|null, pagespeed_mobile?: number|null}} [anreicherung]
 * @returns {Array<{schluessel: string, beschriftung: string, wert: string, art: 'gut'|'fehlt'|'unbekannt'}>}
 */
export function befundZeilen(anreicherung) {
  const a = anreicherung || {};
  return [
    { schluessel: 'ssl',       beschriftung: 'SSL',       ...jaNein(a.has_ssl) },
    { schluessel: 'impressum', beschriftung: 'Impressum', ...jaNein(a.has_impressum) },
    { schluessel: 'pagespeed', beschriftung: 'PageSpeed', ...pagespeed(a.pagespeed_mobile) },
  ];
}

/** Ein Befund ohne Zeitpunkt ist nicht einzuordnen. */
export function geprueftAmText(anreicherung) {
  const zeitpunkt = anreicherung && anreicherung.geprueft_am;
  return zeitpunkt ? `Geprüft am ${zeitpunkt}` : 'Noch nicht geprüft';
}
