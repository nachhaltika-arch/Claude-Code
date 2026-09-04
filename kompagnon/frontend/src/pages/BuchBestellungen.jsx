import React, { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';

/**
 * Die Warteschlange der Druckbestellungen (BUCH-07, L-115).
 *
 * **Warum es diese Seite gibt.** `fulfillment_status` stand seit dem Bau des
 * Bestellwegs auf `queued` und wurde von niemandem gelesen. Ein Kaeufer haette
 * gezahlt, und sein Buch stuende in einer Datenbankzeile, die kein Mensch
 * aufschlaegt — dieselbe Klasse, die diesen Bestand fuenfmal getroffen hat.
 *
 * **Es gibt keine BoD-Schnittstelle.** Der Ablauf ist bewusst Handarbeit:
 * einmal in der Woche die Liste oeffnen, CSV ziehen, bei BoD als
 * Direktbestellung aufgeben, Sendungsnummern zurueckschreiben.
 *
 * **Der Export ist ein POST und wird als Datei zusammengesetzt.** Er setzt die
 * Zeilen auf `exported`; ein `<a href>` koennte den Anmeldekopf ohnehin nicht
 * mitschicken, und ein Vorauslader duerfte die Warteschlange nicht leeren.
 */

const STATUS_TEXT = {
  awaiting_payment: 'Zahlung offen',
  queued: 'Offen',
  exported: 'Exportiert',
  shipped: 'Versendet',
};

const VARIANTE_TEXT = { print: 'Druck', bundle: 'Bündel', pdf: 'PDF' };

const euro = (cents) =>
  ((cents || 0) / 100).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });

const datum = (wert) => (wert ? new Date(wert).toLocaleDateString('de-DE') : '—');

function Kennzahl({ titel, wert }) {
  return (
    <div style={{
      flex: '1 1 160px', background: 'var(--surface)',
      border: '1px solid var(--border-light)', borderRadius: 'var(--r-sm)',
      padding: '12px 14px',
    }}>
      <div style={{
        fontSize: 12, fontWeight: 900, color: 'var(--text-tertiary)',
        textTransform: 'uppercase', letterSpacing: '.08em',
      }}>{titel}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
        {wert}
      </div>
    </div>
  );
}

export default function BuchBestellungen() {
  const { token } = useAuth();
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');
  const [hinweis, setHinweis] = useState('');
  const [laeuft, setLaeuft] = useState(false);
  const [filter, setFilter] = useState({ status: '', variant: '', from_date: '', to_date: '' });
  const [nummern, setNummern] = useState({});

  const kopf = { Authorization: `Bearer ${token}` };

  const laden = useCallback(async () => {
    const abfrage = new URLSearchParams(
      Object.entries(filter).filter(([, w]) => w),
    ).toString();
    // **Der Pfad steht als Ganzes da, die Abfrage haengt aussen an.** Zuerst
    // stand hier `…/orders${abfrage ? `?${abfrage}` : ''}` — eine Zeile, die
    // `test_frontend_adressen` nicht mehr lesen kann: Sie vergleicht Aufrufe
    // mit Routen Abschnitt fuer Abschnitt, und ein Ausdruck hinter dem
    // letzten Abschnitt zaehlt als eigener. Der Waechter hatte recht, und
    // lesbarer ist es auch.
    const basis = `${API_BASE_URL}/api/book/orders`;
    try {
      const antwort = await fetch(
        abfrage ? `${basis}?${abfrage}` : basis,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`);
      setDaten(await antwort.json());
      setFehler('');
    } catch (e) {
      setFehler(`Liste nicht ladbar: ${e.message}`);
    }
  }, [filter, token]);

  useEffect(() => { laden(); }, [laden]);

  const exportieren = async () => {
    setLaeuft(true);
    setHinweis('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/book/orders/export`, {
        method: 'POST', headers: kopf,
      });
      if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`);
      const datei = await antwort.blob();
      // Der Dateiname steht im Kopf der Antwort; er traegt das Datum des
      // Laufs. Ihn hier neu zu bauen hiesse, dieselbe Regel zweimal zu
      // schreiben — und die zweite laeuft irgendwann auseinander.
      const kopfzeile = antwort.headers.get('content-disposition') || '';
      const treffer = kopfzeile.match(/filename="?([^"]+)"?/);
      const adresse = URL.createObjectURL(datei);
      const verweis = document.createElement('a');
      verweis.href = adresse;
      verweis.download = treffer ? treffer[1] : 'bod-bestellungen.csv';
      document.body.appendChild(verweis);
      verweis.click();
      verweis.remove();
      URL.revokeObjectURL(adresse);
      setHinweis('Die Datei liegt im Download-Ordner. Die Bestellungen stehen jetzt auf „Exportiert".');
      await laden();
    } catch (e) {
      setFehler(`Export fehlgeschlagen: ${e.message}`);
    } finally {
      setLaeuft(false);
    }
  };

  const versendet = async (bestellung) => {
    const sendung = (nummern[bestellung.id] || '').trim();
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/book/orders/${bestellung.id}/fulfillment`,
        {
          method: 'PATCH',
          headers: { ...kopf, 'Content-Type': 'application/json' },
          body: JSON.stringify({ fulfillment_status: 'shipped', tracking_number: sendung }),
        },
      );
      if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`);
      const ergebnis = await antwort.json();
      setHinweis(ergebnis.benachrichtigt
        ? `${bestellung.order_number}: versendet, der Kunde ist benachrichtigt.`
        : `${bestellung.order_number}: versendet — die Benachrichtigung ging nicht raus.`);
      await laden();
    } catch (e) {
      setFehler(`Nicht speicherbar: ${e.message}`);
    }
  };

  const zelle = { padding: '8px 10px', fontSize: 13, color: 'var(--text-primary)' };
  const kopfzelle = {
    ...zelle, fontSize: 12, fontWeight: 900, color: 'var(--text-tertiary)',
    textTransform: 'uppercase', letterSpacing: '.06em', textAlign: 'left',
  };
  const feld = {
    fontSize: 13, padding: '6px 8px', borderRadius: 'var(--r-sm)',
    border: '1px solid var(--border-light)', background: 'var(--surface)',
    color: 'var(--text-primary)',
  };

  const offen = daten?.offen || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          Buchbestellungen
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
          Gedruckte Ausgaben zum Aufgeben bei BoD. Es gibt keine Schnittstelle
          dorthin — die Liste wird exportiert und von Hand bestellt.
        </p>
        {daten && (
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: '2px 0 0' }}>
            {daten.gesamt === daten.bestellungen.length
              ? `${daten.gesamt} Bestellungen in dieser Auswahl`
              : `${daten.bestellungen.length} von ${daten.gesamt} in dieser Auswahl angezeigt`}
          </p>
        )}
      </div>

      {fehler && (
        <div role="alert" style={{
          padding: '10px 12px', borderRadius: 'var(--r-sm)', fontSize: 13,
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>{fehler}</div>
      )}
      {hinweis && (
        <div role="status" style={{
          padding: '10px 12px', borderRadius: 'var(--r-sm)', fontSize: 13,
          background: 'var(--status-success-bg)', color: 'var(--status-success-text)',
        }}>{hinweis}</div>
      )}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Kennzahl titel="Offen" wert={offen} />
        <Kennzahl titel="Exportiert" wert={daten?.exportiert ?? '—'} />
        <Kennzahl titel="Versendet" wert={daten?.versendet ?? '—'} />
        <Kennzahl titel="Umsatz laufender Monat" wert={euro(daten?.umsatz_monat_cents)} />
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Status{' '}
          <select style={feld} value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}>
            <option value="">alle</option>
            {Object.entries(STATUS_TEXT).map(([wert, text]) => (
              <option key={wert} value={wert}>{text}</option>
            ))}
          </select>
        </label>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Variante{' '}
          <select style={feld} value={filter.variant}
            onChange={(e) => setFilter({ ...filter, variant: e.target.value })}>
            <option value="">alle</option>
            <option value="print">Druck</option>
            <option value="bundle">Bündel</option>
          </select>
        </label>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          von{' '}
          <input type="date" style={feld} value={filter.from_date}
            onChange={(e) => setFilter({ ...filter, from_date: e.target.value })} />
        </label>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          bis{' '}
          <input type="date" style={feld} value={filter.to_date}
            onChange={(e) => setFilter({ ...filter, to_date: e.target.value })} />
        </label>

        <button type="button" onClick={exportieren} disabled={offen === 0 || laeuft}
          style={{
            marginLeft: 'auto', fontSize: 13, fontWeight: 700, padding: '8px 14px',
            borderRadius: 'var(--r-sm)', border: 'none', cursor: offen === 0 ? 'default' : 'pointer',
            background: offen === 0 ? 'var(--bg-app)' : 'var(--brand-primary)',
            color: offen === 0 ? 'var(--text-tertiary)' : 'var(--text-on-brand)',
          }}>
          {laeuft ? 'wird erzeugt…' : `CSV für BoD exportieren (${offen})`}
        </button>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 900 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
              <th style={kopfzelle}>Bestellnr.</th>
              <th style={kopfzelle}>Datum</th>
              <th style={kopfzelle}>Name</th>
              <th style={kopfzelle}>Firma</th>
              <th style={kopfzelle}>Ort</th>
              <th style={kopfzelle}>Variante</th>
              <th style={kopfzelle}>Zahlung</th>
              <th style={kopfzelle}>Abwicklung</th>
              <th style={kopfzelle}>Sendungsnummer</th>
            </tr>
          </thead>
          <tbody>
            {(daten?.bestellungen || []).map((b) => (
              <tr key={b.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={zelle}>{b.order_number}</td>
                <td style={zelle}>{datum(b.created_at)}</td>
                <td style={zelle}>{`${b.first_name} ${b.last_name}`.trim() || '—'}</td>
                <td style={zelle}>{b.company || '—'}</td>
                <td style={zelle}>{b.ship_city || '—'}</td>
                <td style={zelle}>{VARIANTE_TEXT[b.variant] || b.variant}</td>
                <td style={zelle}>{b.payment_status === 'paid' ? 'bezahlt' : b.payment_status}</td>
                <td style={zelle}>{STATUS_TEXT[b.fulfillment_status] || b.fulfillment_status}</td>
                <td style={zelle}>
                  {b.fulfillment_status === 'shipped' ? (b.tracking_number || '—') : (
                    <span style={{ display: 'flex', gap: 6 }}>
                      <input
                        aria-label={`Sendungsnummer für ${b.order_number}`}
                        placeholder="Sendungsnummer"
                        value={nummern[b.id] || ''}
                        onChange={(e) => setNummern({ ...nummern, [b.id]: e.target.value })}
                        style={{ ...feld, width: 140 }} />
                      <button type="button" onClick={() => versendet(b)}
                        disabled={b.payment_status !== 'paid'}
                        title={b.payment_status !== 'paid'
                          ? 'Erst wenn die Zahlung bestätigt ist'
                          : 'Als versendet markieren'}
                        style={{
                          fontSize: 12, fontWeight: 700, padding: '6px 10px',
                          borderRadius: 'var(--r-sm)', border: '1px solid var(--border-light)',
                          background: 'var(--surface)', color: 'var(--text-primary)',
                          cursor: b.payment_status === 'paid' ? 'pointer' : 'default',
                        }}>versendet</button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {daten && daten.bestellungen.length === 0 && (
              <tr><td style={{ ...zelle, color: 'var(--text-tertiary)' }} colSpan={9}>
                Keine Bestellung in dieser Auswahl.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
