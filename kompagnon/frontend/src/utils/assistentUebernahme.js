/**
 * Die zwei Entscheidungen im Assistenten, die falsch sein können, ohne dass
 * man es am Bildschirm sofort sieht — deshalb liegen sie hier und nicht in
 * der Komponente.
 *
 * 1. Was passiert mit dem, was der Nutzer schon geschrieben hat, wenn er
 *    einen Vorschlag übernimmt? (Antwort: es bleibt stehen.)
 * 2. Wann gilt ein Feldhinweis als „schon gesehen"? (Antwort: gleiches Feld
 *    und gleicher Text — ein anderer Hinweis zum selben Feld darf kommen.)
 */

/** Hängt den Vorschlag an vorhandenen Text an, statt ihn zu ersetzen. */
export function textUebernehmen(vorhanden, vorschlag) {
  const alt = (vorhanden || '').trim();
  const neu = (vorschlag || '').trim();
  if (!neu) return alt;
  if (!alt) return neu;
  if (alt.includes(neu)) return alt;
  return `${alt}\n${neu}`;
}

/** Der Schlüssel, unter dem ein gezeigter Hinweis gemerkt wird. */
export function hinweisSchluessel(feld, hinweise) {
  return `${feld || ''}:${(hinweise || []).join(' ')}`;
}

/**
 * Entscheidet, ob ein Feldbefund dem Nutzer gezeigt wird.
 * `gesehen` ist ein Set von Schlüsseln und wird hier nicht verändert.
 */
export function zeigeHinweis(feld, befund, gesehen) {
  if (!befund || befund.brauchbar) return '';
  const text = (befund.hinweise || []).join(' ');
  if (!text) return '';
  if (gesehen && gesehen.has(hinweisSchluessel(feld, befund.hinweise))) return '';
  return text;
}
