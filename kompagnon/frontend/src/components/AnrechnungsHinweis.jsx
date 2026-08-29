/**
 * Der Hinweis auf eine offene Anrechnung beim Anlegen eines Deals
 * (L-100, ORDERS_08 Schritt 4).
 *
 * **Hier entscheidet sich, ob das Ganze etwas nützt.** Die Prüfroute im
 * Backend kann noch so richtig rechnen — wenn niemand sie sieht, wird die
 * Anrechnung trotzdem vergessen. Der Kunde erinnert sich immer, und es ist
 * genau der Moment, in dem er Vertrauen fassen soll.
 *
 * **Auffällig, nicht unscheinbar.** ORDERS_08 verlangt das ausdrücklich, und
 * die Tool-CI hält Gelb (`--kc-accent`) für den aktiven Zustand vor. Eine
 * graue Zeile zwischen zwanzig anderen ist dasselbe wie keine.
 *
 * **Eigene Komponente und nicht in `Deals.jsx` hinein.** Die Seite hat über
 * 600 Zeilen; eine Prüfung, die dort eingewachsen ist, lässt sich nicht
 * einzeln prüfen — und ORDERS_08 sagt: „Ändere nichts an der Deal-Logik
 * selbst. Wir ergänzen eine Prüfung."
 *
 * **Ein Fehler beim Abruf blendet den Hinweis aus, statt das Formular zu
 * stören.** Wer gerade einen Deal anlegt, soll das zu Ende bringen können;
 * die Anrechnung ist wichtig, aber sie ist nicht der Vorgang.
 */
import React, { useEffect, useState } from 'react';
import API_BASE_URL from '../config';

/** Cent → „149,00 €". */
export function euro(cents) {
  return `${((cents || 0) / 100).toFixed(2).replace('.', ',')} €`;
}

/** Die Abzugsposition, wie sie im Angebot steht. */
export function abzugsposition(anrechnung) {
  return {
    position: `Anrechnung ${anrechnung.product_code} `
      + `(Bestellung ${anrechnung.order_number})`,
    quantity: 1,
    // **Negativ, nicht als Rabattfeld.** Eine Abzugsposition steht im
    // Angebot, wird mitgerechnet und ist im PDF sichtbar; ein stiller Rabatt
    // auf die Summe ist für den Kunden nicht nachvollziehbar.
    unit_price: -(anrechnung.betrag_cents || 0) / 100,
    product_id: null,
    sort_order: 999,
  };
}

export default function AnrechnungsHinweis({ email, kopfzeilen, onUebernehmen }) {
  const [offen, setOffen] = useState([]);
  const [summe, setSumme] = useState(0);

  useEffect(() => {
    const adresse = (email || '').trim();
    if (!adresse) {
      setOffen([]);
      setSumme(0);
      return undefined;
    }

    // `abgebrochen` verhindert, dass eine späte Antwort zu einer inzwischen
    // gewechselten Firma den Hinweis setzt — sonst steht dort die Anrechnung
    // des vorigen Kunden.
    let abgebrochen = false;

    fetch(`${API_BASE_URL}/api/shop/credit-check`
          + `?email=${encodeURIComponent(adresse)}`,
          { headers: kopfzeilen })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (abgebrochen || !d) return;
        setOffen(Array.isArray(d.anrechnungen) ? d.anrechnungen : []);
        setSumme(d.summe_cents || 0);
      })
      .catch(() => {
        if (!abgebrochen) setOffen([]);
      });

    return () => { abgebrochen = true; };
  }, [email, kopfzeilen]);

  if (!offen.length) return null;

  return (
    <div
      data-testid="anrechnung-hinweis"
      role="status"
      style={{
        border: '2px solid var(--kc-accent, #FAE600)',
        background: 'var(--kc-accent-soft, rgba(250, 230, 0, .12))',
        borderRadius: 10,
        padding: '12px 14px',
        margin: '10px 0',
        fontSize: 13,
        lineHeight: 1.6,
      }}
    >
      <p style={{ fontWeight: 700, margin: 0 }}>
        {offen.length === 1
          ? `Offene Anrechnung über ${euro(summe)}`
          : `${offen.length} offene Anrechnungen über zusammen ${euro(summe)}`}
      </p>

      <ul style={{ margin: '6px 0 8px', paddingLeft: 18 }}>
        {offen.map((a) => (
          <li key={a.order_number}>
            {euro(a.betrag_cents)} — Bestellung {a.order_number}
            {a.gueltig_bis ? `, gültig bis ${a.gueltig_bis}` : ''}
            {typeof a.tage_uebrig === 'number'
              ? ` (noch ${a.tage_uebrig} Tage)`
              : ''}
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => onUebernehmen(offen)}
        style={{
          background: 'var(--kc-dark)', color: 'var(--text-inverse)',
          border: 'none', borderRadius: 8, padding: '8px 14px',
          fontSize: 13, fontWeight: 700, minHeight: 40, cursor: 'pointer',
        }}
      >
        Im Angebot berücksichtigen
      </button>
    </div>
  );
}
