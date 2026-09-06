import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';
import { datumKurz } from '../../utils/datum';

/**
 * Bezahlte Leistungen abrufen (L-160 Rang 6).
 *
 * **Der Befund.** Zwei Positionen des Leistungsverzeichnisses konnte der Kunde
 * nicht anfordern, obwohl er sie monatlich bezahlt: die Rücksicherung und die
 * eine neue Unterseite im Jahr. „Selten gebraucht, aber im Ernstfall dringend
 * — und dann sucht niemand nach der Telefonnummer."
 *
 * **Der Knopf löst nichts aus, er meldet an.** Eine Rücksicherung ist
 * Handarbeit am Datenbestand; sie auf Klick zu starten wäre die gefährlichste
 * Automatik im Haus. Deshalb steht neben jedem Abruf, **was danach geschieht**
 * — sonst rät der Kunde, ob gleich etwas passiert oder jemand zurückruft.
 *
 * **Ohne laufendes Abo steht hier nichts.** Eine Leistung ohne Vertrag hat
 * niemand zugesagt.
 */
export default function AbrufbareLeistungen({ token }) {
  const [abrufe, setAbrufe] = useState([]);
  const [laeuft, setLaeuft] = useState(null);
  const [fehler, setFehler] = useState('');

  const laden = useCallback(async () => {
    const res = await fetch(`${API_BASE_URL}/api/portal/abrufe`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setAbrufe((await res.json()).abrufe || []);
  }, [token]);

  useEffect(() => { if (token) laden().catch(() => {}); }, [token, laden]);

  const anfordern = async (nummer) => {
    setLaeuft(nummer); setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/abrufe/${nummer}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: '{}',
      });
      if (!res.ok) throw new Error('Die Anforderung konnte nicht aufgenommen werden.');
      await laden();
    } catch (e) {
      setFehler(e.message);
    } finally {
      setLaeuft(null);
    }
  };

  if (!abrufe.length) return null;

  return (
    <section style={S.rahmen}>
      <h2 style={S.h2}>Aus Ihrem Abo abrufen</h2>
      {fehler && <p style={S.fehler}>{fehler}</p>}
      <ul style={S.liste}>
        {abrufe.map(a => (
          <li key={a.nummer} style={S.zeile}>
            <span style={S.mitte}>
              <span style={S.titel}>{a.titel}</span>
              <span style={S.warum}>
                {a.offen
                  ? `Angefordert am ${datumKurz(a.angefordert_am)}. ${a.danach}`
                  : `${a.warum} · ${a.frequenz}`}
              </span>
              {/* Was nach dem Klick geschieht, steht **vorher** da — nicht
                  erst in der Bestätigung. Wer eine Rücksicherung anfordert,
                  soll wissen, dass sie überschreibt. */}
              {!a.offen && <span style={S.danach}>{a.danach}</span>}
            </span>
            {a.offen ? (
              <span style={S.marke}>angefordert</span>
            ) : (
              <button style={S.knopf} onClick={() => anfordern(a.nummer)}
                      disabled={laeuft === a.nummer}>
                {laeuft === a.nummer ? 'Wird gesendet …' : a.knopf}
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

const S = {
  rahmen: { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, padding: 22, marginTop: 20 },
  h2: { fontSize: 13, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', margin: '0 0 14px' },
  liste: { listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 4 },
  zeile: { display: 'flex', gap: 16, alignItems: 'flex-start', padding: '14px 0', borderTop: '1px solid var(--border-light)', flexWrap: 'wrap' },
  mitte: { flex: '1 1 320px', display: 'flex', flexDirection: 'column', gap: 3 },
  titel: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' },
  warum: { fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.55, maxWidth: '58ch' },
  danach: { fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.55, maxWidth: '58ch', marginTop: 2 },
  knopf: { flex: 'none', fontWeight: 700, fontSize: 13, padding: '9px 16px', borderRadius: 6, border: '1px solid var(--brand-primary)', background: 'none', color: 'var(--brand-primary)', cursor: 'pointer' },
  marke: { flex: 'none', fontSize: 12, fontWeight: 700, padding: '5px 12px', borderRadius: 999, background: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
  fehler: { fontSize: 13, color: 'var(--status-danger-text)', margin: '0 0 12px' },
};
