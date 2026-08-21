/**
 * Was mit der Maus geht, muss auch mit der Tastatur gehen.
 *
 * Lücke L-17, dritte Klasse. Gemessen am 21.08.2026: **167 klickbare
 * Elemente**, die eine Tastatur nicht erreicht — 165 `<div>`, ein `<span>`,
 * eine `<tr>`. Sie tragen ein `onClick` und sonst nichts: keine Rolle, keinen
 * Platz in der Tabulatorreihenfolge, keine Tastenbehandlung.
 *
 * Das ist **WCAG 2.1.1 (Keyboard), Stufe A** — die strengste Stufe, und die
 * einzige, bei der ein Ausfall nicht „schlechter bedienbar" heißt, sondern
 * „gar nicht bedienbar". Wer keine Maus führen kann, kommt an diese Stellen
 * nicht heran.
 *
 * Drei Dinge gehören zusammen, und keines genügt allein:
 *
 *   role="button"      sagt Hilfsmitteln, was das Element ist
 *   tabIndex={0}       stellt es in die Tabulatorreihenfolge
 *   onKeyDown          führt aus, was der Klick ausführt
 *
 * `aufTaste` liefert das dritte. Enter und Leertaste sind die beiden Tasten,
 * die eine Schaltfläche auslösen; die Leertaste scrollt sonst die Seite,
 * deshalb `preventDefault`.
 */

/** Löst denselben Vorgang aus wie ein Klick — bei Enter und Leertaste. */
export function aufTaste(handler) {
  return (ereignis) => {
    if (ereignis.key !== 'Enter' && ereignis.key !== ' ') return;
    // Die Leertaste scrollt sonst die Seite, während sie die Schaltfläche
    // auslöst — beides zugleich ist für den Nutzer ein Sprung ins Nichts.
    ereignis.preventDefault();
    if (typeof handler === 'function') handler(ereignis);
  };
}
