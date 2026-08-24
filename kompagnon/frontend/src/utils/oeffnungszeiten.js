// Öffnungszeiten zwischen Eingabezeilen und gespeichertem JSON (L-15, L-99).
//
// Warum es das gibt: `schema.org/LocalBusiness` verlangt Öffnungszeiten, und
// der SEO/GEO-Agent antwortet ohne sie mit 400. Gespeichert wird JSON — sieben
// Spalten wären sieben Migrationen beim ersten Sonderfall („Sa nach
// Vereinbarung"). Eingegeben werden Zeilen, weil niemand JSON tippen will.
//
// **Kaputte Eingaben ergeben ein leeres Verzeichnis, keinen Absturz.** Das
// Feld steht in einem Formular; ein halb getippter Eintrag darf die Seite
// nicht zerlegen. Dieselbe Regel wie in `services/betriebsadresse.py`.

/** `{"Mo-Fr": "08:00-17:00"}` → `Mo-Fr 08:00-17:00` je Zeile. */
export function oeffnungszeitenAlsText(roh) {
  if (!roh) return '';
  let gelesen;
  try {
    gelesen = typeof roh === 'string' ? JSON.parse(roh) : roh;
  } catch {
    // Was schon als Text drinsteht, bleibt sichtbar — sonst verschwindet die
    // Eingabe des Nutzers beim ersten Zeichen, das kein gültiges JSON ergibt.
    return typeof roh === 'string' ? roh : '';
  }
  if (!gelesen || typeof gelesen !== 'object' || Array.isArray(gelesen)) return '';
  return Object.entries(gelesen).map(([tage, zeit]) => `${tage} ${zeit}`).join('\n');
}

/** `Mo-Fr 08:00-17:00` je Zeile → `{"Mo-Fr": "08:00-17:00"}`. */
export function oeffnungszeitenAlsJson(text) {
  const eintraege = {};
  for (const zeile of (text || '').split('\n')) {
    const sauber = zeile.trim();
    if (!sauber) continue;
    // Erstes Leerzeichen trennt Tage von Zeit: „Mo-Do 08:00-17:00".
    // Fehlt die Zeit, bleibt der Wert leer statt zu raten.
    const luecke = sauber.indexOf(' ');
    const tage = luecke === -1 ? sauber : sauber.slice(0, luecke);
    const zeit = luecke === -1 ? '' : sauber.slice(luecke + 1).trim();
    eintraege[tage] = zeit;
  }
  return Object.keys(eintraege).length ? JSON.stringify(eintraege) : '';
}
