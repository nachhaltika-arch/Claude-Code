import { useEffect, useState } from 'react';
import API_BASE_URL from '../config';
import { loadJson } from '../utils/apiRequest';

/**
 * Was bei diesem Betrieb zuletzt geschah — immer sichtbar (L-82).
 *
 * **Der Befund.** Aus dem HubSpot-Audit vom 19.08.2026: Dort steht der
 * Verlauf auf der Datensatzseite und nicht hinter einem Reiter. Bei uns lag
 * er in dreien — Mails im einen, Analysen im anderen, Nachrichten im dritten.
 * Wer beim Anruf erst klicken muss, um zu sehen, was zuletzt war, sieht es
 * nicht.
 *
 * Der Verlauf steht deshalb **neben** dem Reiterbereich und bleibt stehen,
 * egal welcher Reiter offen ist.
 *
 * Zwei Mail-Protokolle führt der Server zusammen (`services/lead_verlauf.py`);
 * ein Ereignis, das aus beiden stammt, trägt beide Quellen — sichtbar im
 * Titelhinweis, damit nachvollziehbar bleibt, wo es herkommt.
 */

const ZEICHEN = {
  angelegt: '•',
  audit:    '◆',
  projekt:  '▣',
  briefing: '✎',
  email:    '✉',
  kontakt:  '☎',
};

/** Datum kurz, wie man es am Telefon sagt. */
function kurzesDatum(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

export default function BetriebVerlauf({ leadId, token }) {
  const [ereignisse, setEreignisse] = useState([]);
  const [laedt, setLaedt] = useState(true);
  const [fehler, setFehler] = useState(null);

  useEffect(() => {
    if (!leadId) return undefined;
    let abgemeldet = false;

    (async () => {
      setLaedt(true);
      setFehler(null);
      try {
        const daten = await loadJson(
          `${API_BASE_URL}/api/leads/${leadId}/verlauf`,
          { headers: { Authorization: `Bearer ${token}` } },
          { context: 'Verlauf' },
        );
        if (!abgemeldet) setEreignisse(daten?.ereignisse || []);
      } catch (e) {
        // **Nicht still verschlucken.** Ein leerer Verlauf und ein Verlauf,
        // der nicht geladen werden konnte, sehen sonst gleich aus — und das
        // Erste heisst „hier war nichts", das Zweite „wir wissen es nicht".
        if (!abgemeldet) setFehler(e?.message || 'Der Verlauf konnte nicht geladen werden.');
      } finally {
        if (!abgemeldet) setLaedt(false);
      }
    })();

    return () => { abgemeldet = true; };
  }, [leadId, token]);

  return (
    <section
      aria-label="Verlauf des Betriebs"
      style={{
        background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)', padding: 14,
        display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0,
      }}
    >
      <h3 style={{
        margin: 0, fontSize: 12, fontWeight: 600, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: 'var(--text-tertiary)',
        fontFamily: 'var(--font-sans)',
      }}>
        Zuletzt geschehen
      </h3>

      {laedt && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Wird geladen…</div>
      )}

      {!laedt && fehler && (
        <div style={{ fontSize: 12, color: 'var(--status-danger-text)' }}>{fehler}</div>
      )}

      {!laedt && !fehler && ereignisse.length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          Für diesen Betrieb ist noch nichts vermerkt.
        </div>
      )}

      {!laedt && !fehler && ereignisse.length > 0 && (
        <ol style={{ listStyle: 'none', margin: 0, padding: 0,
                     display: 'flex', flexDirection: 'column', gap: 10 }}>
          {ereignisse.map((e, i) => (
            <li
              key={`${e.zeitpunkt}-${e.art}-${i}`}
              style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}
            >
              <span aria-hidden="true" style={{
                color: 'var(--brand-primary-mid)', fontSize: 12, lineHeight: '16px',
                width: 12, textAlign: 'center', flexShrink: 0,
              }}>
                {ZEICHEN[e.art] || '•'}
              </span>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  title={`Quelle: ${(e.quellen || []).join(', ')}`}
                  style={{ fontSize: 12, color: 'var(--text-primary)',
                           lineHeight: '16px', wordBreak: 'break-word' }}
                >
                  {e.titel}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>
                  {kurzesDatum(e.zeitpunkt)}
                  {e.hinweis ? ` · ${e.hinweis}` : ''}
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
