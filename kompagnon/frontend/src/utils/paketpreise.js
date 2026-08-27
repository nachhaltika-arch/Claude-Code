/**
 * Paketpreise — eine Quelle, und zwar die, aus der auch abgerechnet wird.
 *
 * Befund L-29 (nachgemessen 19.08.2026, geschlossen 21.08.): Derselbe Preis
 * stand an vier Stellen und war bereits auseinandergelaufen. Premium hatte im
 * Frontend zweimal 2.500, waehrend `products` — die Tabelle, aus der die
 * Stripe-Sitzung ihren Betrag zieht — 2.800 trug. Der Kunde las 2.500 und
 * bezahlte 2.800. Kompagnon stand in `Landing.jsx` mit 3.500 gegen 2.000.
 *
 * Die Preise kommen jetzt aus `GET /api/payments/packages` (oeffentlich, ohne
 * Anmeldung). Was hier bleibt, ist die **Darstellung**: Farben, Abzeichen,
 * Reihenfolge, Merkmalslisten — Dinge, die keine zweite Wahrheit erzeugen
 * koennen.
 *
 * Ist der Preis nicht zu holen, steht dort **kein Preis** — nicht der letzte
 * bekannte. Dieselbe Entscheidung wie in `payments.paketbezeichnung`:
 * lieber nackt als falsch.
 */

/** Deutsche Schreibweise ohne Nachkommastellen: 2000 → "2.000". */
export function preisAnzeige(euro) {
  const zahl = Number(euro);
  if (!Number.isFinite(zahl) || zahl <= 0) return null;
  return Math.round(zahl).toLocaleString('de-DE');
}

/**
 * Legt die Antwort des Servers ueber die oertliche Darstellung.
 *
 * @param {Array<{id: string}>} darstellung  Farben, Merkmale, Reihenfolge
 * @param {Object} ausApi  Antwort von /api/payments/packages, Schluessel = slug
 * @returns {Array} dieselbe Reihenfolge, je Eintrag `preis`, `preisLabel`,
 *                  `preisBekannt` und — falls der Server ihn kennt — `name`
 */
export function paketeZusammenfuehren(darstellung, ausApi) {
  const vomServer = ausApi && typeof ausApi === 'object' ? ausApi : {};

  return (darstellung || []).map((paket) => {
    const zeile = vomServer[paket.id];
    const preis = zeile ? Number(zeile.price_eur) : null;
    const label = preisAnzeige(preis);

    return {
      ...paket,
      name: (zeile && zeile.name) || paket.name,
      preis: label === null ? null : preis,
      preisLabel: label,
      preisBekannt: label !== null,
      // Kaeuflich ist, was der Server liefert: `/api/payments/packages` gibt
      // nur Pakete mit Status `live` heraus, und `create-checkout` nimmt auch
      // nur solche an. Beim Wechsel auf die Websprint-Produkte (L-97,
      // 23.08.2026) wurden drei Pakete archiviert, waehrend ihre
      // Verkaufsseiten den Kauf weiter anboten — der Aufruf endete in einem
      // 400er. Wer einen Kaufknopf zeigt, prueft das hier.
      //
      // Bewusst nicht dasselbe wie `preisBekannt`: Das beantwortet „kennen
      // wir den Preis", nicht „darf das jemand kaufen". Heute faellt beides
      // zusammen; ein Paket mit Preis, das nicht verkauft wird, wuerde die
      // beiden trennen.
      verkaeuflich: Boolean(zeile),
    };
  });
}

/** Was in der Vergleichszeile „Preis" steht, wenn der Server nichts liefert. */
export const PREIS_UNBEKANNT = 'auf Anfrage';

/** Die Preiszeile einer Vergleichstabelle — aus denselben zusammengefuehrten
 *  Paketen, damit Karte und Tabelle nicht getrennt veralten koennen. */
export function preisZeile(pakete) {
  return (pakete || []).map((p) =>
    p.preisBekannt ? `${p.preisLabel} €` : PREIS_UNBEKANNT,
  );
}
