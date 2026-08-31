/**
 * Was der Käufer auf der Danke-Seite sehen soll — je nach Zahlungsstand.
 *
 * **Warum eigene Datei.** Die Seite selbst rendert; **welche Aussage** zu
 * welchem Status gehört, ist eine Entscheidung, und die gehört an eine
 * Stelle, an der man sie prüfen kann, ohne einen Browser zu starten.
 *
 * **Der Anlass (31.08.2026, L-105).** `GET /api/shop/orders/{nr}/status`
 * existiert seit ORDERS_04 und **ruft ihn niemand**. Die Danke-Seite stammt
 * aus ORDERS_03 — aus der Zeit, als es die Zahlungsrückmeldung noch nicht
 * gab — und sagt seither unverändert „Sobald die Zahlung bei uns bestätigt
 * ist, erhalten Sie die Bestätigung per E-Mail". Auch dann noch, wenn die
 * Zahlung längst bestätigt und die Datei längst verschickt ist.
 *
 * **Kein Downloadlink auf dieser Seite, und das ist Absicht.** Der Endpunkt
 * gibt bewusst nur Nummer, Status und Produktschlüssel heraus — kein Token,
 * keine Beträge, keine Anschrift. Die Bestellnummer steht im Browserverlauf;
 * wer daraus einen Abruf machen könnte, hätte eine Datenschutzlücke in einer
 * öffentlichen Route. Die Datei kommt über die E-Mail, wie gebaut.
 */

/** Die Zustände, die `payment_status` annehmen kann. */
export const OFFEN = 'created';
export const BEZAHLT = 'paid';
export const AUSGELIEFERT = 'delivered';
export const GESCHEITERT = 'failed';

/**
 * @param {string|null} status  `payment_status` der Bestellung, oder null,
 *                              solange nichts abgefragt wurde
 * @param {boolean} abgelaufen  ob die Wartezeit überschritten ist
 * @returns {{titel: string, text: string, art: 'wartet'|'gut'|'fehler'}}
 */
export function aussage(status, abgelaufen = false) {
  if (status === BEZAHLT || status === AUSGELIEFERT) {
    return {
      art: 'gut',
      titel: 'Zahlung bestätigt',
      text: 'Die E-Mail mit Ihrem Download und der Rechnung ist unterwegs. '
        + 'Sehen Sie bitte auch im Spam-Ordner nach.',
    };
  }
  if (status === GESCHEITERT) {
    return {
      art: 'fehler',
      titel: 'Zahlung nicht abgeschlossen',
      text: 'Die Zahlung ist nicht durchgegangen. Es wurde nichts abgebucht. '
        + 'Sie können den Kauf erneut versuchen.',
    };
  }
  if (abgelaufen) {
    // **Nicht „es dauert noch".** Wer nach zwei Minuten immer noch dasselbe
    // liest, hält die Seite für kaputt. Hier steht, was er tun kann.
    return {
      art: 'wartet',
      titel: 'Bestellung eingegangen',
      text: 'Die Bestätigung der Zahlung steht noch aus. Sie erhalten die '
        + 'E-Mail, sobald sie da ist — Sie müssen diese Seite nicht offen '
        + 'lassen.',
    };
  }
  return {
    art: 'wartet',
    titel: 'Bestellung eingegangen',
    text: 'Wir warten auf die Bestätigung der Zahlung. Das dauert in der '
      + 'Regel wenige Sekunden.',
  };
}

/**
 * Ob weiter gefragt werden soll.
 *
 * **Ein Endzustand wird nicht weiter abgefragt** — sonst läuft die Schleife,
 * solange der Reiter offen ist, und erzeugt Last für eine Antwort, die sich
 * nicht mehr ändert.
 */
export function weiterFragen(status, versuche, hoechstens) {
  if (status === BEZAHLT || status === AUSGELIEFERT || status === GESCHEITERT) {
    return false;
  }
  return versuche < hoechstens;
}
