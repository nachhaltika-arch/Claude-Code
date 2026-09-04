/**
 * Beträge in deutscher Schreibweise — an einer Stelle.
 *
 * **Warum das eine eigene Datei ist (04.09.2026).** Die Formatierung stand
 * als lokale Hilfsfunktion im Shop; mit dem Pflege-Abo im Kundenkonto hätte
 * sie ein zweites Mal danebengestanden. Ein zweiter Ort für dieselbe Regel
 * ist ein Ort, an dem sie sich unterscheidet — und bei Geldbeträgen sieht
 * man den Unterschied sofort, ohne zu wissen, welcher der richtige ist.
 *
 * **Zwei Eingaben, weil es zwei Quellen gibt.** Der Produktkatalog führt
 * Euro (`price_brutto`), die Abo-Rechnung führt Cent (`brutto_cent`).
 * Umrechnen beim Aufrufer wäre genau die Stelle, an der jemand einmal durch
 * hundert teilt und einmal nicht.
 */

/** Ein Betrag in Euro: `4165` → „4.165,00 €". */
export function euro(betrag) {
  return Number(betrag || 0).toLocaleString('de-DE', {
    style: 'currency', currency: 'EUR', minimumFractionDigits: 2,
  });
}

/** Ein Betrag in Cent: `9401` → „94,01 €". */
export function euroAusCent(cent) {
  return euro(Number(cent || 0) / 100);
}
