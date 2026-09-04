import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';
import { datumKurz } from '../utils/datum';

/**
 * Inhaltsänderungen: Kontostand und Änderungswunsch (Rang 1).
 *
 * **Warum ein Kontostand und nicht nur ein Formular.** „Bis 90 Minuten je
 * Monat" ist ein Guthaben. Ohne sichtbaren Stand wird es entweder nicht
 * genutzt — dann zahlt der Kunde für nichts — oder überzogen, dann streitet
 * man hinterher über Minuten.
 *
 * **In Minuten, nicht in Stunden.** Das Datenblatt sagt Minuten; „0,5 h
 * verbleibend" wäre dieselbe Zahl in einer Sprache, die der Kunde nicht
 * spricht.
 */
export default function Inhaltsguthaben({ token }) {
  const [daten, setDaten] = useState(null);
  const [text, setText] = useState('');
  const [seite, setSeite] = useState('');
  const [fehler, setFehler] = useState('');
  const [sendet, setSendet] = useState(false);
  const [offen, setOffen] = useState(false);

  const laden = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/inhalt`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Konnte nicht geladen werden (${res.status})`);
      setDaten(await res.json());
    } catch (e) { setFehler(e.message); }
  };

  useEffect(() => { if (token) laden(); }, [token]);   // eslint-disable-line

  const senden = async (e) => {
    e.preventDefault();
    setSendet(true); setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/inhalt`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ beschreibung: text, seite }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Der Wunsch ließ sich nicht senden.');
      setText(''); setSeite(''); setOffen(false);
      await laden();
    } catch (e2) { setFehler(e2.message); }
    finally { setSendet(false); }
  };

  if (!daten) return null;
  const { guthaben, anfragen = [], hinweis } = daten;
  if (!guthaben && !anfragen.length) return null;

  return (
    <section style={S.rahmen}>
      <h2 style={S.h1}>Inhaltsänderungen</h2>

      <div style={S.karte}>
        {guthaben ? (
          <>
            <div style={S.stand}>
              <span style={S.zahl}>{guthaben.rest_minuten}</span>
              <span style={S.einheit}>von {guthaben.kontingent_minuten} Minuten frei</span>
              <span style={S.monat}>im {monatName(guthaben.monat)}</span>
            </div>
            {guthaben.ueberzogen && (
              <p style={S.warnung}>
                Ihr Guthaben für diesen Monat ist aufgebraucht. Wünsche nehmen wir
                weiter an — wir sprechen vorher mit Ihnen, was sie kosten.
              </p>
            )}
            {guthaben.eintraege.length > 0 && (
              <div style={S.eintraege}>
                {guthaben.eintraege.map((e, i) => (
                  <div key={i} style={S.eintrag}>
                    <span style={S.min}>{e.minuten} Min.</span>
                    <span style={S.taetigkeit}>{e.taetigkeit || 'Inhaltsänderung'}</span>
                    <span style={S.leise}>{e.erfasst_am ? datumKurz(e.erfasst_am) : ''}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <p style={S.leise}>{hinweis || 'Für diesen Monat ist kein Pflege-Abo hinterlegt.'}</p>
        )}

        {!offen ? (
          <button style={S.knopf} onClick={() => setOffen(true)}>Änderung anfordern</button>
        ) : (
          <form onSubmit={senden} style={S.form}>
            <label style={S.label} htmlFor="inhalt-was">Was soll geändert werden?</label>
            <textarea id="inhalt-was" style={S.feld} rows={3} value={text} required
                      onChange={(e) => setText(e.target.value)}
                      placeholder="Zum Beispiel: Die Öffnungszeiten am Samstag ändern sich auf 9 bis 13 Uhr." />
            <label style={S.label} htmlFor="inhalt-wo">Auf welcher Seite? (wenn Sie es wissen)</label>
            <input id="inhalt-wo" style={S.feld} value={seite}
                   onChange={(e) => setSeite(e.target.value)} placeholder="Startseite" />
            <div style={S.reihe}>
              <button type="submit" style={S.knopf} disabled={sendet}>
                {sendet ? 'Wird gesendet …' : 'Wunsch senden'}
              </button>
              <button type="button" style={S.knopfLeise} onClick={() => setOffen(false)}>
                Abbrechen
              </button>
            </div>
          </form>
        )}
        {fehler && <p style={S.fehler}>{fehler}</p>}
      </div>

      {anfragen.length > 0 && (
        <div style={S.karte}>
          <h3 style={S.h2}>Ihre Wünsche</h3>
          {anfragen.map((a) => (
            <div key={a.id} style={S.zeile}>
              <span style={S.beschreibung}>{a.beschreibung}</span>
              <span style={MARKE[a.status] || MARKE.offen}>{WORT[a.status] || a.status}</span>
              <span style={S.leise}>
                {a.erledigt_am ? `erledigt am ${datumKurz(a.erledigt_am)}`
                               : `angefragt am ${datumKurz(a.angefragt_am)}`}
              </span>
              {a.notiz && <span style={S.notiz}>{a.notiz}</span>}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                'August', 'September', 'Oktober', 'November', 'Dezember'];
function monatName(m) {
  const [j, mo] = (m || '').split('-');
  return MONATE[Number(mo) - 1] ? `${MONATE[Number(mo) - 1]} ${j}` : m;
}

const WORT = { offen: 'offen', in_arbeit: 'in Arbeit', erledigt: 'erledigt',
               abgelehnt: 'abgelehnt' };
const marke = { fontSize: 12, fontWeight: 700, padding: '3px 10px',
                borderRadius: 999, whiteSpace: 'nowrap', flex: 'none' };
const MARKE = {
  offen: { ...marke, background: 'var(--bg-app)', color: 'var(--text-secondary)', boxShadow: 'inset 0 0 0 1px var(--border-subtle)' },
  in_arbeit: { ...marke, background: 'var(--bg-app)', color: 'var(--brand-primary)', boxShadow: 'inset 0 0 0 1px var(--brand-primary)' },
  erledigt: { ...marke, background: 'var(--status-success-bg)', color: 'var(--status-success)' },
  abgelehnt: { ...marke, background: 'var(--bg-app)', color: 'var(--text-tertiary)', boxShadow: 'inset 0 0 0 1px var(--border-subtle)' },
};

const S = {
  rahmen: { marginTop: 32 },
  h1: { fontWeight: 900, letterSpacing: '-0.025em', fontSize: 20, margin: '0 0 12px', color: 'var(--text-primary)' },
  h2: { fontWeight: 900, fontSize: 14, textTransform: 'uppercase', letterSpacing: '-0.02em', margin: '0 0 12px', color: 'var(--text-secondary)' },
  karte: { background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 24, marginBottom: 12 },
  stand: { display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap', marginBottom: 16 },
  zahl: { fontFamily: 'var(--font-mono, monospace)', fontSize: 40, fontWeight: 700, lineHeight: 1, color: 'var(--brand-primary)' },
  einheit: { fontSize: 16, color: 'var(--text-primary)' },
  monat: { fontSize: 14, color: 'var(--text-tertiary)' },
  warnung: { fontSize: 14, color: 'var(--text-secondary)', background: 'var(--bg-app)', borderRadius: 6, padding: '10px 14px', margin: '0 0 16px', maxWidth: '62ch' },
  eintraege: { borderTop: '1px solid var(--border-subtle)', marginBottom: 16 },
  eintrag: { display: 'flex', gap: 12, alignItems: 'baseline', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 14 },
  min: { fontFamily: 'var(--font-mono, monospace)', flex: 'none', color: 'var(--text-primary)' },
  taetigkeit: { flex: 1, color: 'var(--text-secondary)' },
  form: { display: 'flex', flexDirection: 'column', gap: 6, maxWidth: '62ch' },
  label: { fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)', marginTop: 8 },
  feld: { font: 'inherit', fontSize: 15, padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-subtle)', background: 'var(--bg-app)', color: 'var(--text-primary)' },
  reihe: { display: 'flex', gap: 8, marginTop: 12 },
  knopf: { fontWeight: 900, fontSize: 14, padding: '12px 20px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--brand-primary)', color: '#fff' },
  knopfLeise: { fontWeight: 700, fontSize: 14, padding: '12px 20px', borderRadius: 6, border: '1px solid var(--border-subtle)', cursor: 'pointer', background: 'none', color: 'var(--text-secondary)' },
  zeile: { display: 'flex', gap: 12, alignItems: 'baseline', flexWrap: 'wrap', padding: '10px 0', borderTop: '1px solid var(--border-subtle)' },
  beschreibung: { flex: 1, minWidth: 200, fontSize: 15, color: 'var(--text-primary)' },
  notiz: { flexBasis: '100%', fontSize: 13, color: 'var(--text-tertiary)' },
  leise: { fontSize: 13, color: 'var(--text-tertiary)' },
  fehler: { color: 'var(--status-danger-text)', fontSize: 14, marginTop: 12 },
};
