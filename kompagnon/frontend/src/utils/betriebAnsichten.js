// Benannte Ansichten der Betriebsliste (L-83).
//
// **Der Befund.** Die Liste kennt vier Achsen — Suche, Status, Quelle, Phase —
// und dazu die Sortierung. Wer täglich denselben Blick braucht („wer ist neu
// reingekommen?"), stellt ihn jedes Mal neu ein: vier Auswahlfelder für eine
// Frage, die sich nicht ändert. Aus dem HubSpot-Audit vom 19.08.2026: Dort
// liegen gespeicherte Ansichten als Reiter über der Liste, nicht als
// Filterzustand, den jeder für sich neu herstellt.
//
// **Warum fest verdrahtet und nicht speicherbar.** Eigene Ansichten je Nutzer
// wären Serverzustand, Verwaltung und ein zweiter Bildschirm — für einen
// Innendienst, der aus wenigen Personen besteht. Der Nutzen steckt in den
// paar Blicken, die alle brauchen. Die Auswahlfelder bleiben daneben stehen:
// Wer etwas anderes sehen will, stellt es weiter selbst ein und landet dann
// auf „Eigene Auswahl".
//
// Alle Funktionen geben neue Objekte zurück und fassen die Eingabe nicht an.

/** Die Achsen, die eine Ansicht festlegt. Die Suche gehört bewusst nicht dazu. */
const ACHSEN = ['status', 'quelle', 'phase', 'sortierung'];

/**
 * Die Reiter über der Liste, in dieser Reihenfolge.
 *
 * Jede Ansicht setzt **alle** Achsen. Eine, die eine Achse offen ließe, würde
 * den vorigen Zustand erben — und derselbe Reiter zeigte zweimal Verschiedenes.
 */
export const BETRIEB_ANSICHTEN = [
  {
    id: 'alle',
    label: 'Alle',
    hinweis: 'Der ganze Bestand, alphabetisch',
    filter: { status: 'alle', quelle: 'alle', phase: 'alle', sortierung: 'name' },
  },
  {
    id: 'neu',
    label: 'Neu',
    // Ohne Phase heißt: noch niemand hat sich damit befasst. Neueste zuerst,
    // weil hier die Reaktionszeit zählt.
    hinweis: 'Noch keiner Phase zugeordnet, neueste zuerst',
    filter: { status: 'alle', quelle: 'alle', phase: 'offen', sortierung: 'date' },
  },
  {
    id: 'im_gespraech',
    label: 'Im Gespräch',
    hinweis: 'Laufende Gespräche, neueste zuerst',
    filter: { status: 'alle', quelle: 'alle', phase: 'im_gespraech', sortierung: 'date' },
  },
  {
    id: 'kunden',
    label: 'Kunden',
    hinweis: 'Bestandskunden, alphabetisch',
    filter: { status: 'alle', quelle: 'alle', phase: 'kunde', sortierung: 'name' },
  },
  {
    id: 'chancen',
    label: 'Chancen',
    // Interessenten nach Score: die Liste, aus der der nächste Anruf kommt.
    hinweis: 'Interessenten mit dem höchsten Score zuerst',
    filter: { status: 'alle', quelle: 'alle', phase: 'interessent', sortierung: 'score' },
  },
];

const nachId = (kennung) => BETRIEB_ANSICHTEN.find((a) => a.id === kennung);

/**
 * Eine Ansicht auf den Listenzustand legen.
 *
 * Die Suche bleibt stehen — wer sucht und dann den Reiter wechselt, will sie
 * behalten und nicht ein zweites Mal tippen. Eine unbekannte Kennung ändert
 * nichts, statt die Liste auf einen halben Zustand zu setzen.
 */
export function ansichtAnwenden(zustand = {}, kennung) {
  const ansicht = nachId(kennung);
  if (!ansicht) return { ...zustand };
  return { ...zustand, ...ansicht.filter };
}

/**
 * Welcher Reiter passt zum aktuellen Zustand? `null`, wenn keiner passt.
 *
 * Wichtig für die Anzeige: Leuchtet ein Reiter, obwohl die Liste etwas anderes
 * zeigt, ist die Beschriftung eine Falschaussage.
 */
export function ansichtFinden(zustand = {}) {
  const treffer = BETRIEB_ANSICHTEN.find((a) =>
    ACHSEN.every((achse) => zustand[achse] === a.filter[achse]),
  );
  return treffer ? treffer.id : null;
}

/** Der Nutzer hat sich etwas zusammengestellt, das keinem Reiter entspricht. */
export function istEigeneAuswahl(zustand = {}) {
  return ansichtFinden(zustand) === null;
}
