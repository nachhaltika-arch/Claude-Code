// Welcher Knopf auf dem Betriebsbildschirm der eine ist.
//
// Warum es das gibt: In der Kopfleiste standen sechs Knoepfe gleichberechtigt
// nebeneinander — Audit starten, Kaltakquise starten, Bearbeiten, Neu pruefen,
// Briefing starten, Projekt anlegen. Wer den Bildschirm oeffnet, muss erst
// lesen, um zu wissen, was jetzt dran ist (UX-13).
//
// „Die eine Aktion" ist keine feste: Sie haengt davon ab, wie weit der Betrieb
// ist. Ohne Audit gibt es nichts zu verschicken; ist gewonnen, faengt das
// Projekt an. Deshalb eine Funktion statt einer Farbe im Markup.
//
// Gibt `null` zurueck, wenn sich nichts aufdraengt — nach einem gesendeten
// Angebot wartet man auf Antwort, nicht auf einen Knopf. Dann ist kein Knopf
// hervorgehoben, und das ist ehrlicher als einer auf Verdacht.

/**
 * @param {{hatAudit?: boolean, hatProjekt?: boolean, hatEmail?: boolean, status?: string}} [zustand]
 * @returns {'audit'|'kaltakquise'|'projekt'|'zum_projekt'|'stammdaten'|null}
 */
export function naechsterSchritt(zustand = {}) {
  const { hatAudit = false, hatProjekt = false, hatEmail = false, status = 'new' } = zustand;

  if (hatProjekt) return 'zum_projekt';
  if (!hatAudit) return 'audit';
  if (status === 'won') return 'projekt';
  if (status === 'lost' || status === 'proposal_sent') return null;
  if (hatEmail) return 'kaltakquise';
  return 'stammdaten';
}
