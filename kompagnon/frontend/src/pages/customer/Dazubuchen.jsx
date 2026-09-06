import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';
import { euroAusCent } from '../../utils/geld';
import SeitenTitel from '../../components/ui/SeitenTitel';

/**
 * „Dazubuchen" — was ein Bestandskunde zusätzlich beauftragen kann.
 *
 * **Der Bestätigungsschritt ist der Kern dieser Seite, nicht die Kachel.** Ein
 * Wechsel auf Pflege Pro heißt Lastschrift über 177,31 € im Monat; ein GEO-
 * Auftrag heißt 1.428 € brutto. Wer so etwas mit einem Klick auslöst, hat es
 * nicht gebucht, sondern sich verklickt. Deshalb: erst der Wortlaut, dann ein
 * Häkchen, dann der Knopf.
 *
 * **Netto und brutto stehen beide da, beschriftet** (Entscheidung David,
 * 04.09.2026). Der Betrieb hat „149 € netto" unterschrieben und bekommt
 * 177,31 € abgebucht — nur eine der beiden Zahlen zu zeigen erzeugt den
 * Anruf, der mit „bei mir steht aber etwas anderes" beginnt.
 *
 * **Was nicht angeboten wird, fehlt nicht stillschweigend.** Ist ein Angebot
 * nicht buchbar, steht der Grund daneben; ein Angebot, das einfach
 * verschwindet, wirft die Frage auf, ob es das noch gibt.
 */
export default function Dazubuchen() {
  const { token } = useAuth();
  const [daten, setDaten] = useState(null);
  const [offen, setOffen] = useState(null);      // welches Angebot bestätigt wird
  const [verstanden, setVerstanden] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState('');
  const [danach, setDanach] = useState('');

  const laden = useCallback(async () => {
    const res = await fetch(`${API_BASE_URL}/api/portal/dazubuchen`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setDaten(await res.json());
    else setFehler(`Konnte nicht geladen werden (${res.status})`);
  }, [token]);

  useEffect(() => { if (token) laden().catch(() => {}); }, [token, laden]);

  const buchen = async (kennung) => {
    setLaeuft(true); setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/dazubuchen/${kennung}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ verstanden: true }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Die Buchung konnte nicht aufgenommen werden.');
      setOffen(null); setVerstanden(false);
      setDanach(d.danach || '');
      await laden();
    } catch (e) {
      setFehler(e.message);
    } finally {
      setLaeuft(false);
    }
  };

  if (!daten) {
    return (
      <div style={S.seite}>
        <SeitenTitel>Dazubuchen</SeitenTitel>
        <h1 style={S.h1}>Leistungen dazubuchen</h1>
        <p style={S.leise}>{fehler || 'Wird geladen …'}</p>
      </div>
    );
  }

  return (
    <div style={S.seite}>
      <SeitenTitel>Dazubuchen</SeitenTitel>
      <h1 style={S.h1}>Leistungen dazubuchen</h1>
      <p style={S.unter}>
        Alles, was Sie zu Ihrem laufenden Vertrag hinzunehmen können. Preise
        netto und brutto, mit Zahlungsbedingung und Laufzeit.
      </p>

      {fehler && <p style={S.fehler}>{fehler}</p>}
      {danach && <p style={S.hinweis}>{danach}</p>}
      {!daten.darf_buchen && (
        <p style={S.leise}>
          Buchen kann ein Zugang, der alles darf. Sie sehen hier, was es gibt.
        </p>
      )}

      {daten.angebote.map(a => (
        <article key={a.kennung} style={{ ...S.karte, borderTopColor: a.buchbar ? 'var(--brand-primary)' : 'var(--border-light)' }}>
          <div style={S.kopf}>
            <span>
              <span style={S.titel}>{a.titel}</span>
              <span style={S.nummer}>{a.nummer}</span>
            </span>
            <span style={S.preis}>
              <b style={S.brutto}>
                {euroAusCent(a.brutto_cent)}{a.einmalig ? ' einmalig' : ' je Monat'}
              </b>
              {/* Beide Zahlen, beschriftet — sonst kommt der Anruf. */}
              <span style={S.netto}>
                {euroAusCent(a.netto_cent)} netto zzgl. {a.steuersatz} % USt.
              </span>
            </span>
          </div>

          <p style={S.dazu}>{a.dazu}</p>
          {a.punkte.length > 0 && (
            <ul style={S.punkte}>{a.punkte.map(p => <li key={p}>{p}</li>)}</ul>
          )}

          <dl style={S.bedingungen}>
            <div><dt style={S.dt}>Zahlung</dt><dd style={S.dd}>{a.zahlung}</dd></div>
            <div><dt style={S.dt}>Laufzeit</dt><dd style={S.dd}>{a.laufzeit}</dd></div>
          </dl>

          {a.gebucht ? (
            <p style={S.gebucht}>Gebucht — wir setzen es um und melden uns.</p>
          ) : !a.buchbar ? (
            <p style={S.leise}>{a.grund}</p>
          ) : daten.darf_buchen && (
            offen === a.kennung ? (
              /* **Der Bestätigungsschritt.** Erst hier steht der Rechtstext —
                 vorher wäre er Kleingedrucktes, das niemand liest, und nach
                 dem Klick zu spät. */
              <div style={S.bestaetigen}>
                <p style={S.recht}>{a.rechtstext}</p>
                <label style={S.haken}>
                  <input type="checkbox" checked={verstanden}
                         onChange={e => setVerstanden(e.target.checked)} />
                  <span>
                    Ich habe die Bedingungen gelesen und buche verbindlich
                    {a.einmalig ? '.' : ` ab dem 1. ${monatName(daten.ab_monat)}.`}
                  </span>
                </label>
                <div style={S.knoepfe}>
                  <button style={S.knopf} disabled={!verstanden || laeuft}
                          onClick={() => buchen(a.kennung)}>
                    {laeuft ? 'Wird gebucht …' : 'Verbindlich buchen'}
                  </button>
                  <button style={S.abbrechen}
                          onClick={() => { setOffen(null); setVerstanden(false); }}>
                    Abbrechen
                  </button>
                </div>
              </div>
            ) : (
              <button style={S.knopf}
                      onClick={() => { setOffen(a.kennung); setVerstanden(false); setDanach(''); }}>
                {a.titel}
              </button>
            )
          )}
        </article>
      ))}
    </div>
  );
}

const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                'August', 'September', 'Oktober', 'November', 'Dezember'];
function monatName(abMonat) {
  const teil = Number((abMonat || '').split('-')[1]);
  return MONATE[teil - 1] || abMonat;
}

const S = {
  seite: { maxWidth: 760, margin: '0 auto', padding: '0 0 40px' },
  h1: { fontSize: 22, fontWeight: 900, letterSpacing: '-.02em', color: 'var(--text-primary)', margin: '0 0 6px' },
  unter: { fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 22px', maxWidth: '62ch' },
  karte: { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderTop: '3px solid', borderRadius: 8, padding: '22px 24px', marginBottom: 16 },
  kopf: { display: 'flex', gap: 16, justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: 10 },
  titel: { fontSize: 17, fontWeight: 900, letterSpacing: '-.015em', color: 'var(--text-primary)', display: 'block' },
  nummer: { fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono, monospace)' },
  preis: { textAlign: 'right', display: 'flex', flexDirection: 'column', gap: 2 },
  brutto: { fontSize: 17, fontWeight: 900, color: 'var(--text-primary)' },
  netto: { fontSize: 12, color: 'var(--text-tertiary)' },
  dazu: { fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 10px', maxWidth: '62ch' },
  punkte: { margin: '0 0 14px', paddingLeft: 20, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 },
  bedingungen: { margin: '0 0 16px', display: 'flex', flexDirection: 'column', gap: 6 },
  dt: { fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.04em' },
  dd: { fontSize: 13, color: 'var(--text-secondary)', margin: '2px 0 0', lineHeight: 1.55, maxWidth: '62ch' },
  bestaetigen: { borderTop: '2px solid var(--brand-primary)', paddingTop: 16, marginTop: 4 },
  recht: { fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.65, margin: '0 0 14px', maxWidth: '64ch', background: 'var(--bg-app)', padding: '12px 16px', borderRadius: 6 },
  haken: { display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 16, maxWidth: '60ch' },
  knoepfe: { display: 'flex', gap: 12, flexWrap: 'wrap' },
  knopf: { fontWeight: 900, fontSize: 14, padding: '13px 22px', borderRadius: 6, border: 'none', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', cursor: 'pointer' },
  abbrechen: { fontWeight: 700, fontSize: 14, padding: '13px 20px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'none', color: 'var(--text-secondary)', cursor: 'pointer' },
  gebucht: { fontSize: 14, fontWeight: 700, color: 'var(--status-success-text)', margin: 0 },
  hinweis: { fontSize: 14, color: 'var(--status-success-text)', lineHeight: 1.6, margin: '0 0 18px', maxWidth: '64ch' },
  fehler: { fontSize: 13, color: 'var(--status-danger-text)', margin: '0 0 16px' },
  leise: { fontSize: 13, color: 'var(--text-tertiary)', margin: 0, lineHeight: 1.6, maxWidth: '60ch' },
};
