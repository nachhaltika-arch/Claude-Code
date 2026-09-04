import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';
import { datumKurz } from '../utils/datum';

/**
 * Abo, Rechnungen und Zahlungsart — an einer Stelle, weil der Kunde sie als
 * eines denkt: Was zahle ich, womit zahle ich, was habe ich bezahlt.
 *
 * **Die Zahlungsart ändert er bei Stripe, nicht bei uns.** Ein eigenes
 * Kartenformular hieße, Kartendaten durch unseren Server zu führen. Der Knopf
 * holt eine Sitzung im Billing-Portal und leitet dorthin weiter.
 *
 * **Kein toter Knopf.** Ein Betrieb ohne Kauf hat kein Zahlungskonto; dann
 * steht dort ein Satz statt einer Schaltfläche, die ins Leere führt.
 */
export default function Zahlungen({ token }) {
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/portal/zahlungen`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error(`Konnte nicht geladen werden (${res.status})`);
        setDaten(await res.json());
      } catch (e) { setFehler(e.message); }
    })();
  }, [token]);

  const verwalten = async () => {
    setLaeuft(true);
    setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/zahlungen/verwalten`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Die Zahlungsseite ließ sich nicht öffnen.');
      window.location.href = d.url;
    } catch (e) {
      setFehler(e.message);
    } finally { setLaeuft(false); }
  };

  if (!daten) return null;
  const { abos = [], rechnungen = [], zahlungskonto } = daten;
  if (!abos.length && !rechnungen.length && zahlungskonto !== 'vorhanden') return null;

  return (
    <section style={S.rahmen}>
      <h2 style={S.h1}>Zahlungen</h2>

      <div style={S.karte}>
        <h3 style={S.h2}>Laufende Verträge</h3>
        {abos.length === 0
          ? <p style={S.leise}>Zurzeit kein laufendes Abo.</p>
          : abos.map((a, i) => (
              <div key={i} style={S.zeile}>
                <span style={S.stark}>{PRODUKT[a.produkt] || a.produkt}</span>
                <span style={S.leise}>
                  seit {a.start_monat}{a.end_monat ? ` · endet ${a.end_monat}` : ''}
                </span>
              </div>
            ))}
      </div>

      <div style={S.karte}>
        <h3 style={S.h2}>Zahlungsart</h3>
        {zahlungskonto === 'vorhanden' ? (
          <>
            <p style={S.leise}>
              Karte oder Bankeinzug ändern, Abo kündigen, Belege herunterladen —
              alles bei unserem Zahlungsdienst.
            </p>
            <button style={S.knopf} onClick={verwalten} disabled={laeuft}>
              {laeuft ? 'Wird geöffnet …' : 'Zahlungsdaten verwalten'}
            </button>
          </>
        ) : (
          <p style={S.leise}>
            {zahlungskonto === 'dienst_fehlt'
              ? 'Die Zahlungsverwaltung ist gerade nicht erreichbar. Schreiben Sie uns, wir kümmern uns.'
              : 'Für Sie ist noch keine Zahlungsart hinterlegt — das entsteht mit der ersten Buchung.'}
          </p>
        )}
        {fehler && <p style={S.fehler}>{fehler}</p>}
      </div>

      {rechnungen.length > 0 && (
        <div style={S.karte}>
          <h3 style={S.h2}>Ihre Rechnungen</h3>
          {rechnungen.map((r, i) => (
            <div key={i} style={S.zeile}>
              <span style={S.mono}>{r.invoice_number || '—'}</span>
              <span style={S.leise}>{r.line_item}</span>
              <span style={S.betrag}>{geld(r.amount_gross)}</span>
              <span style={r.status === 'bezahlt' ? S.markeOk : S.markeOffen}>
                {r.status === 'bezahlt'
                  ? `bezahlt${r.paid_at ? ` am ${datumKurz(r.paid_at)}` : ''}`
                  : `offen${r.due_date ? ` bis ${datumKurz(r.due_date)}` : ''}`}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

// Die Kennungen kommen aus `services/abo_vertrag`: ABO-BAS, ABO-PRO.
// Erst falsch geraten (abo_bas), dann am laufenden Dienst nachgesehen.
const PRODUKT = { 'ABO-BAS': 'Pflege Basic', 'ABO-PRO': 'Pflege Pro' };

function geld(wert) {
  const n = Number(wert);
  return Number.isFinite(n)
    ? n.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })
    : '—';
}

const marke = {
  fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 999,
  whiteSpace: 'nowrap', flex: 'none',
};
const S = {
  rahmen: { marginTop: 32 },
  h1: { fontWeight: 900, letterSpacing: '-0.025em', fontSize: 20, margin: '0 0 12px', color: 'var(--text-primary)' },
  h2: { fontWeight: 900, fontSize: 14, textTransform: 'uppercase', letterSpacing: '-0.02em', margin: '0 0 12px', color: 'var(--text-secondary)' },
  karte: { background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 24, marginBottom: 12 },
  zeile: { display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap', padding: '10px 0', borderTop: '1px solid var(--border-subtle)' },
  stark: { fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' },
  mono: { fontFamily: 'var(--font-mono, monospace)', fontSize: 13, color: 'var(--text-primary)', flex: 'none' },
  betrag: { fontFamily: 'var(--font-mono, monospace)', fontSize: 14, marginLeft: 'auto', color: 'var(--text-primary)' },
  leise: { fontSize: 14, color: 'var(--text-tertiary)', margin: '0 0 12px', maxWidth: '60ch', flex: 1 },
  markeOk: { ...marke, background: 'var(--status-success-bg)', color: 'var(--status-success)' },
  markeOffen: { ...marke, background: 'var(--bg-app)', color: 'var(--text-secondary)', boxShadow: 'inset 0 0 0 1px var(--border-subtle)' },
  knopf: { fontWeight: 900, fontSize: 14, padding: '12px 20px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--brand-primary)', color: '#fff' },
  fehler: { color: 'var(--status-danger-text)', fontSize: 14, marginTop: 12 },
};
