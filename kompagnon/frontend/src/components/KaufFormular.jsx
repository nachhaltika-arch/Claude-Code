import React, { useState } from 'react';
import API_BASE_URL from '../config';
import { VERZICHTSTEXT } from '../inhalte/rechtstexte';

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
 * **Der Widerrufsverzicht ist zwei Dinge zugleich.** Die Sperre dahinter
 * steht im Backend, damit sie nicht vergessen wird. Ein Verbraucher ohne
 * Verzicht bekommt eine 400 mit klarer Begründung — die zeigt dieses Formular
 * unverändert an.
 *
 * **Zwei Funde beim Nachziehen auf ORDERS_05 (29.08.2026):**
 *
 * **(1) Hier stand ein selbst geschriebener Rechtssatz.** Das Verzichts-
 * Häkchen trug den Wortlaut „Ich verlange die sofortige Bereitstellung und
 * weiß, dass ich damit mein Widerrufsrecht verliere…". Genau das verbietet
 * ORDERS_05. Der Satz war plausibel, und darin lag die Gefahr: Niemand hätte
 * ihn zur Prüfung gegeben, weil er geprüft aussah. Er kommt jetzt aus
 * `inhalte/rechtstexte.js` und steht dort bis zur anwaltlichen Fassung als
 * sichtbare Markierung.
 *
 * **(2) „Privat" war vorbelegt.** Ein Häkchen „Ich kaufe als Unternehmen"
 * bedeutete unangehakt „Privatperson" — also eine Vorbelegung, die über das
 * Widerrufsrecht entscheidet, ohne dass jemand sie getroffen hat. ORDERS_05
 * verlangt eine Pflichtauswahl ohne Vorbelegung; deshalb zwei Auswahlfelder
 * und ein dritter Zustand „noch nichts gewählt".
 */
export default function KaufFormular({ produkt, onAbbrechen }) {
  const [daten, setDaten] = useState({
    buyer_name: '', buyer_email: '', buyer_address: '',
    buyer_company: '', buyer_vat_id: '',
    // `null` heisst „noch nichts gewaehlt" und ist nicht dasselbe wie
    // `false`. Der Unterschied entscheidet ueber das Widerrufsrecht.
    is_business: null, terms_accepted: false, withdrawal_waived: false,
  });
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  const setze = (feld) => (e) => setDaten((d) => ({
    ...d, [feld]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
  }));

  const kaufen = async () => {
    setFehler('');
    if (daten.is_business === null) {
      // Vor dem Netzaufruf: Die Antwort des Servers waere „is_business muss
      // ein Boolescher Wert sein" — richtig und fuer einen Kaeufer nutzlos.
      setFehler('Bitte wählen Sie, ob Sie als Privatperson oder als '
                + 'Unternehmen kaufen. Davon hängt Ihr Widerrufsrecht ab.');
      return;
    }
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

      {/* Pflichtauswahl ohne Vorbelegung (ORDERS_05). Zwei Auswahlfelder
          statt eines Haeckchens: Ein unangehaktes Kaestchen ist eine
          getroffene Entscheidung, die niemand getroffen hat. */}
      <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
        <legend style={beschriftung}>Ich kaufe als *</legend>
        <div style={{ display: 'flex', gap: 18, marginTop: 2 }}>
          <label style={{ ...haken, alignItems: 'center' }}>
            <input type="radio" name="kf-kaeuferart" id="kf-privat"
                   checked={daten.is_business === false}
                   onChange={() => setDaten((d) => ({
                     ...d, is_business: false, buyer_company: '', buyer_vat_id: '',
                   }))} />
            <span>Privatperson</span>
          </label>
          <label style={{ ...haken, alignItems: 'center' }}>
            <input type="radio" name="kf-kaeuferart" id="kf-firma-art"
                   checked={daten.is_business === true}
                   onChange={() => setDaten((d) => ({
                     ...d, is_business: true, withdrawal_waived: false,
                   }))} />
            <span>Unternehmen</span>
          </label>
        </div>
      </fieldset>

      {/* Firma und USt-IdNr. erscheinen nur, wenn sie gebraucht werden. Zwei
          Felder, die einen Verbraucher nichts angehen, machen das Formular
          länger und die Abbruchquote höher. */}
      {daten.is_business === true && (
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

      {/* Ein Haeckchen auf einen Text, den man nicht lesen kann, ist keine
          Einbeziehung. Neues Fenster, damit die eingegebenen Daten nicht
          verloren gehen — `noopener`, sonst bekaeme die geoeffnete Seite
          Zugriff auf `window.opener`. */}
      <label style={haken}>
        <input type="checkbox" data-testid="agb" checked={daten.terms_accepted}
               onChange={setze('terms_accepted')} />
        <span>
          Ich akzeptiere die{' '}
          <a href="/agb" target="_blank" rel="noopener noreferrer"
             style={{ textDecoration: 'underline' }}>AGB</a>
          {' '}und die{' '}
          <a href="/datenschutz" target="_blank" rel="noopener noreferrer"
             style={{ textDecoration: 'underline' }}>Datenschutzerklärung</a>.
        </span>
      </label>

      {/* Nur für Verbraucher. Ein Unternehmen hat kein Widerrufsrecht nach
          § 355 BGB, und ein Häkchen für einen Verzicht auf ein Recht, das
          man nicht hat, ist eine Irreführung. */}
      {daten.is_business === false && (
        <>
          <label style={haken}>
            <input type="checkbox" data-testid="verzicht"
                   checked={daten.withdrawal_waived}
                   onChange={setze('withdrawal_waived')} />
            {/* Der Wortlaut steht in `inhalte/rechtstexte.js` und nicht hier:
                Er muss an drei Stellen gleich lauten — Formular, Belehrung,
                Bestellbestaetigung. Drei Kopien driften auseinander. */}
            <span data-testid="verzicht-text">{VERZICHTSTEXT}</span>
          </label>
          <p style={{ ...haken, fontSize: 12 }}>
            Ihre{' '}
            <a href="/widerruf" target="_blank" rel="noopener noreferrer"
               style={{ textDecoration: 'underline', fontWeight: 700 }}>
              Widerrufsbelehrung
            </a>
            {' '}— bitte vor dem Kauf lesen.
          </p>
        </>
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
