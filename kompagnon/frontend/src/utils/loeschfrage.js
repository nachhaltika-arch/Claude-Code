// Was eine Löschfrage nennen muss.
//
// Im Werkzeug gibt es drei Arten, eine Löschung zu bestätigen: die
// Browserfrage (26 Stellen), einen eigenen kleinen Dialog (Kursliste) und
// einen mit Vorschau dessen, was zuerst geht (Projekte löschen).
//
// Sie zu vereinheitlichen wäre die falsche Arbeit. Der Unterschied, auf den es
// ankommt, ist nicht die Bauform, sondern **was auf dem Spiel steht**:
//
//   - Eine einzelne, ersetzbare Sache  → die Browserfrage genügt
//   - Etwas mit Anhang                 → die Frage muss den Anhang nennen
//   - Etwas Unwiderrufliches mit vielen Abhängigkeiten → eigener Dialog
//     mit Vorschau (siehe ProjekteLoeschenModal)
//
// Diese Funktion deckt die mittlere Stufe ab: Sie baut einen Satz, der sagt,
// **was** verschwindet — nicht nur, dass etwas verschwindet.

/** Ein Wort in Ein- oder Mehrzahl, je nach Anzahl. */
export function anzahlWort(anzahl, einzahl, mehrzahl) {
  return `${anzahl} ${anzahl === 1 ? einzahl : mehrzahl}`;
}

/**
 * `loeschfrage('Modul', 'Grundlagen', [[3, 'Lektion', 'Lektionen']])`
 *   → 'Modul „Grundlagen" löschen?\n\nDamit geht auch: 3 Lektionen.'
 */
export function loeschfrage(art, name, anhang = []) {
  const kopf = name ? `${art} „${name}" löschen?` : `${art} löschen?`;
  const teile = anhang
    .filter(([anzahl]) => anzahl > 0)
    .map(([anzahl, einzahl, mehrzahl]) => anzahlWort(anzahl, einzahl, mehrzahl));

  if (teile.length === 0) return kopf;
  return `${kopf}\n\nDamit geht auch: ${teile.join(', ')}.`;
}
