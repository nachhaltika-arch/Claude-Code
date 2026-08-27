import React, { useState } from 'react';
import API_BASE_URL from '../config';

/**
 * Die Käuferdaten vor dem Bezahlvorgang (L-100, ORDERS_03).
 *
 * **Kein `<form>` mit Standardabsenden.** ORDERS_03 verlangt das
 * ausdrücklich: Ein abgesendetes Formular lädt die Seite neu, und die
 * Weiterleitung zu Stripe geht dabei verloren.
 *
 * **Fehler stehen im Formular, nicht in der Konsole.** Wer eine Zustimmung
 * vergisst, soll lesen, welche — und nicht einen Knopf sehen, der nichts tut.
 *
 * **Der Widerrufsverzicht ist zwei Dinge zugleich.** Die Beschriftung folgt
 * in ORDERS_05 im Wortlaut; die Sperre dahinter steht schon im Backend, damit
 * sie nicht vergessen wird. Ein Verbraucher ohne Verzicht bekommt eine 400
 * mit klarer Begründung — die zeigt dieses Formular unverändert an.
 */
export default function KaufFormular({ produkt, onAbbrechen }) {
  const [daten, setDaten] = useState({
    buyer_name: '', buyer_email: '', buyer_address: '',
    buyer_company: '', buyer_vat_id: '',
    is_business: false, terms_accepted: false, withdrawal_waived: false,
  });
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  const setze = (feld) => (e) => setDaten((d) => ({
    ...d, [feld]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
  }));

  const kaufen = async () => {
    setFehler('');
    setLaeuft(true);
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/shop/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...daten, product_code: produkt.slug }),
      });
      const ergebnis = await antwort.json().catch(() => ({}));
      if (!antwort.ok) {
        setFehler(ergebnis.detail || 'Der Kauf konnte nicht gestartet werden.');
        return;
      }
      // Weiterleitung zu Stripe. `assign` statt `replace`: Wer abbricht,
      // soll mit dem Zurück-Knopf hierher zurückfinden.
      window.location.assign(ergebnis.checkout_url);
    } catch {
      setFehler('Verbindungsfehler — es wurde nichts bestellt.');
    } finally {
      setLaeuft(false);
    }
  };

  const feld = {
    width: '100%', padding: '10px 12px', fontSize: 14,
    border: '1px solid var(--border-medium)', borderRadius: 8,
    boxSizing: 'border-box', fontFamily: 'var(--font-sans)',
  };
  const beschriftung = {
    display: 'block', fontSize: 12, fontWeight: 700, marginBottom: 4,
    color: 'var(--text-secondary)', textTransform: 'uppercase',
    letterSpacing: '.06em',
  };
  const haken = {
    display: 'flex', gap: 10, alignItems: 'flex-start',
    fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div>
        <label style={beschriftung} htmlFor="kf-name">Name *</label>
        <input id="kf-name" style={feld} value={daten.buyer_name}
               onChange={setze('buyer_name')} autoComplete="name" />
      </div>
      <div>
        <label style={beschriftung} htmlFor="kf-mail">E-Mail *</label>
        <input id="kf-mail" type="email" style={feld} value={daten.buyer_email}
               onChange={setze('buyer_email')} autoComplete="email" />
      </div>
      <div>
        <label style={beschriftung} htmlFor="kf-adresse">Anschrift *</label>
        <input id="kf-adresse" style={feld} value={daten.buyer_address}
               onChange={setze('buyer_address')}
               placeholder="Straße, PLZ Ort" autoComplete="street-address" />
      </div>

      <label style={haken}>
        <input type="checkbox" checked={daten.is_business}
               onChange={setze('is_business')} />
        <span>Ich kaufe als Unternehmen</span>
      </label>

      {/* Firma und USt-IdNr. erscheinen nur, wenn sie gebraucht werden. Zwei
          Felder, die einen Verbraucher nichts angehen, machen das Formular
          länger und die Abbruchquote höher. */}
      {daten.is_business && (
        <>
          <div>
            <label style={beschriftung} htmlFor="kf-firma">Firma</label>
            <input id="kf-firma" style={feld} value={daten.buyer_company}
                   onChange={setze('buyer_company')} autoComplete="organization" />
          </div>
          <div>
            <label style={beschriftung} htmlFor="kf-ustid">USt-IdNr.</label>
            <input id="kf-ustid" style={feld} value={daten.buyer_vat_id}
                   onChange={setze('buyer_vat_id')} />
          </div>
        </>
      )}

      <label style={haken}>
        <input type="checkbox" checked={daten.terms_accepted}
               onChange={setze('terms_accepted')} />
        <span>Ich akzeptiere die AGB und die Datenschutzerklärung.</span>
      </label>

      {/* Nur für Verbraucher. Ein Unternehmen hat kein Widerrufsrecht nach
          § 355 BGB, und ein Häkchen für einen Verzicht auf ein Recht, das
          man nicht hat, ist eine Irreführung. */}
      {!daten.is_business && (
        <label style={haken}>
          <input type="checkbox" checked={daten.withdrawal_waived}
                 onChange={setze('withdrawal_waived')} />
          <span>
            Ich verlange die sofortige Bereitstellung und weiß, dass ich damit
            mein Widerrufsrecht verliere, sobald die Bereitstellung beginnt.
          </span>
        </label>
      )}

      {fehler && (
        <div role="alert" style={{
          background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
          borderRadius: 8, padding: '10px 12px', fontSize: 13, lineHeight: 1.6,
        }}>
          {fehler}
        </div>
      )}

      <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
        <button type="button" onClick={kaufen} disabled={laeuft}
                style={{
                  flex: 1, background: 'var(--kc-dark)', color: 'var(--text-inverse)',
                  border: 'none', borderRadius: 8, padding: '12px 20px',
                  fontSize: 15, fontWeight: 700, minHeight: 48,
                  cursor: laeuft ? 'wait' : 'pointer',
                }}>
          {laeuft ? 'Einen Moment…' : 'Zahlungspflichtig bestellen'}
        </button>
        <button type="button" onClick={onAbbrechen}
                style={{
                  background: 'var(--bg-app)', color: 'var(--text-primary)',
                  border: 'none', borderRadius: 8, padding: '12px 16px',
                  fontSize: 14, minHeight: 48, cursor: 'pointer',
                }}>
          Abbrechen
        </button>
      </div>
    </div>
  );
}
