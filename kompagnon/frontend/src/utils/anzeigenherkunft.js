// Woher der Besucher kam, wenn er ueber eine Anzeige kam (L-86).
//
// **Der Befund.** Das Formular schickte `website_url`, `email` und
// `lead_source` — und sonst nichts. Wer ueber eine Anzeige mit
// `?utm_source=google` auf die Seite kam, verlor seine Herkunft im Moment
// des Absendens. Die Kanalauswertung (L-84) konnte bezahlte Kanaele darum
// nie ausweisen: Die Frage „welcher Kanal bringt Kunden" blieb fuer genau
// die Kanaele offen, die Geld kosten.
//
// Reine Funktion mit der Adresse als Eingabe — damit sie pruefbar ist und
// nicht am `window` haengt.

/** Die drei Felder, die der Server kennt. Mehr wird nicht mitgeschickt. */
export const UTM_FELDER = ['utm_source', 'utm_medium', 'utm_campaign'];

/** So lang ist die Spalte. Laengeres kuerzt auch der Server — hier schon. */
const MAX = 200;

/**
 * Liest die UTM-Angaben aus einer Adresse.
 *
 * Gibt nur zurueck, was da ist: Ein leeres Objekt heisst „keine Herkunft
 * bekannt". Eine geratene Herkunft waere schlimmer als eine fehlende — auf
 * ihr wuerde die Auswertung rechnen.
 */
export function herkunftAusAdresse(adresse) {
  const gefunden = {};
  if (!adresse) return gefunden;

  let parameter;
  try {
    parameter = new URL(adresse, 'https://example.invalid').searchParams;
  } catch {
    // Eine unlesbare Adresse ist kein Grund, das Formular scheitern zu lassen.
    return gefunden;
  }

  for (const feld of UTM_FELDER) {
    const wert = (parameter.get(feld) || '').trim();
    if (wert) gefunden[feld] = wert.slice(0, MAX);
  }
  return gefunden;
}

/** Dasselbe fuer die Adresse, auf der die Seite gerade laeuft. */
export function herkunftDieserSeite() {
  if (typeof window === 'undefined') return {};
  return herkunftAusAdresse(window.location?.href);
}
