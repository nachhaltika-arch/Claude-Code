/**
 * Die Fassung des Standards, gegen die ein Ergebnis entstanden ist.
 *
 * **Warum es das gibt (S6.2, § 11 Punkt 4).** Das Backend setzt seit der
 * Fassung 2026.2 `audit_results.standard_version` und liefert das Feld auch
 * aus. Gelesen hat es am 24.08.2026 kein einziges Bauteil im Frontend. Damit
 * stand im Buch die Zusage, jedes Ergebnis nenne seine Fassung — und im
 * Bericht stand sie nicht.
 *
 * Der Schaden ist nicht nur kosmetisch: Die Audit-Historie rechnet aus dem
 * ersten und dem letzten Ergebnis eine „Verbesserung". Stammen die beiden aus
 * verschiedenen Fassungen, vergleicht sie zwei verschiedene Maßstäbe und nennt
 * das Ergebnis Fortschritt. Genau davor warnt § 11 Punkt 4 mit dem Wort
 * „Trennlinie im Verlauf".
 */

/** Was angezeigt wird — auch dann, wenn nichts vermerkt ist. */
export function fassungText(version) {
  const v = String(version || '').trim();
  // Kein Vermerk heisst: vor Einfuehrung der Kennzeichnung erhoben. Das ist
  // eine Auskunft und keine Vermutung — die Spalte kam mit der Fassung 2026.2.
  return v ? `Fassung ${v}` : 'Fassung nicht vermerkt';
}

/**
 * Dürfen zwei Ergebnisse gegeneinander gerechnet werden?
 *
 * Nur bei gleicher, bekannter Fassung. Zwei leere Vermerke gelten **nicht**
 * als gleich: Unbekannt ist keine Übereinstimmung, sondern eine Wissenslücke.
 */
export function vergleichbar(a, b) {
  const x = String(a || '').trim();
  const y = String(b || '').trim();
  return Boolean(x) && x === y;
}

/** Die im Verlauf vorkommenden Fassungen — für die Frage, ob eine Spalte nötig ist. */
export function fassungenIm(audits) {
  return [...new Set(
    (audits || []).map((a) => String(a?.standard_version || '').trim()),
  )];
}
