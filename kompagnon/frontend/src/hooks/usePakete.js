/**
 * Die Pakete, wie der Server sie kennt — eine Quelle fuer alle Verkaufsflaechen.
 *
 * Holt `GET /api/payments/packages` (oeffentlich, ohne Anmeldung; dieselbe
 * Zeile, aus der die Stripe-Sitzung ihren Betrag zieht) und legt die Antwort
 * ueber die oertliche Darstellung. Siehe `utils/paketpreise.js` fuer das
 * Warum — Luecke L-29.
 */
import { useEffect, useState } from 'react';

import API_BASE_URL from '../config';
import { paketeZusammenfuehren } from '../utils/paketpreise';

export default function usePakete(darstellung) {
  const [ausApi, setAusApi] = useState(null);
  const [laedt, setLaedt] = useState(true);

  useEffect(() => {
    let abgemeldet = false;

    fetch(`${API_BASE_URL}/api/payments/packages`)
      .then((antwort) => (antwort.ok ? antwort.json() : null))
      .then((daten) => {
        if (!abgemeldet) setAusApi(daten);
      })
      .catch(() => {
        // Kein leeres catch: Der Fehler ist sichtbar, weil dann **kein**
        // Preis dasteht statt eines veralteten (L-36, L-29).
        if (!abgemeldet) setAusApi(null);
      })
      .finally(() => {
        if (!abgemeldet) setLaedt(false);
      });

    return () => {
      abgemeldet = true;
    };
  }, []);

  return { pakete: paketeZusammenfuehren(darstellung, ausApi), laedt };
}
