import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';
import { datumKurz } from '../../utils/datum';

/**
 * „Ihre Daten" — Auskunft und Löschung (L-160 Rang 5, Art. 15 und 17 DSGVO).
 *
 * **Der Befund.** Beides ist ein gesetzlicher Anspruch, und beides ging bisher
 * nur über eine Mail an uns. Wer sie nicht beantwortet bekommt, hat einen
 * Verstoß in der Hand — und keine Spur, dass er gefragt hat.
 *
 * **Die Löschung wird beantragt, nicht ausgeführt.** Eine Löschung, die sofort
 * greift, ist bei einem Betrieb ohne zweiten Zugang ein Ausfall ohne Rückweg.
 * Der Antrag ist zugleich der Nachweis des Eingangs; ab ihm läuft die
 * Monatsfrist aus Art. 12.
 *
 * **Die drei Hürden sind ungleich, und die Anzeige sagt das.** Das Abo ist
 * eine Sperre, das Hosting eine Warnung, die Zehnjahresfrist für Rechnungen
 * eine Auskunft. Sie alle gleich darzustellen — drei Häkchen zum Abarbeiten —
 * hieße, § 147 AO als etwas auszugeben, das man ausräumen kann.
 */
export default function MeineDatenRechte({ token }) {
  const [stand, setStand] = useState(null);
  const [offen, setOffen] = useState(false);
  const [wort, setWort] = useState('');
  const [verstanden, setVerstanden] = useState(false);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  const laden = useCallback(async () => {
    const res = await fetch(`${API_BASE_URL}/api/portal/loeschung`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setStand(await res.json());
  }, [token]);

  useEffect(() => { if (token) laden().catch(() => {}); }, [token, laden]);

  const kopieHolen = async () => {
    const res = await fetch(`${API_BASE_URL}/api/portal/datenkopie`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) { setFehler('Die Datenkopie konnte nicht erstellt werden.'); return; }
    const text = JSON.stringify(await res.json(), null, 2);
    const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    /* Der Abruf trägt die Anmeldung im Kopf; die Datei entsteht im Browser
       und verlässt ihn nicht. */
    const a = document.createElement('a');
    a.href = url;
    a.download = `KOMPAGNON-Datenkopie-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  };

  const beantragen = async () => {
    setLaeuft(true); setFehler('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/portal/loeschung`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ bestaetigung: wort, verstanden }),
      });
      const d = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(d.detail || 'Der Antrag konnte nicht aufgenommen werden.');
      setOffen(false); setWort(''); setVerstanden(false);
      await laden();
    } catch (e) {
      setFehler(e.message);
    } finally {
      setLaeuft(false);
    }
  };

  if (!stand) return null;
  const antrag = stand.antrag;

  return (
    <section style={S.rahmen}>
      <h2 style={S.h2}>Ihre Daten</h2>
      <p style={S.satz}>
        Sie haben das Recht, eine Kopie aller Daten zu erhalten, die wir über
        Sie gespeichert haben, und deren Löschung zu verlangen (Art. 15 und 17
        DSGVO).
      </p>

      {fehler && <p style={S.fehler}>{fehler}</p>}

      <div style={S.knoepfe}>
        <button style={S.knopfRand} onClick={kopieHolen}>Datenkopie herunterladen</button>
        {antrag ? (
          <span style={S.beantragt}>
            Löschung beantragt am {datumKurz(antrag.beantragt_am)} — wir melden
            uns bis {datumKurz(antrag.frist_bis)}.
          </span>
        ) : stand.moeglich ? (
          <button style={S.knopfGefahr} onClick={() => setOffen(!offen)}>
            {offen ? 'Abbrechen' : 'Löschung beantragen'}
          </button>
        ) : (
          <span style={S.gesperrt}>{stand.sperrgrund}</span>
        )}
      </div>

      <ul style={S.huerden}>
        {stand.huerden.map(h => (
          <li key={h.titel} style={S.huerde}>
            {/* Status als Farbe **und** Wort — grün heißt hier „ausgeräumt",
                grau heißt „gilt und bleibt". */}
            <span style={{ ...S.punkt, background: farbe(h) }} aria-hidden />
            <span>
              <b style={S.huerdeTitel}>{h.titel}</b>
              <span style={S.huerdeStatus}>{wort_fuer(h)}</span>
              <span style={S.huerdeText}>{h.dazu}</span>
            </span>
          </li>
        ))}
      </ul>

      {offen && !antrag && (
        <div style={S.frage}>
          <p style={S.folgenKopf}>Was mit dem Antrag geschieht:</p>
          <ul style={S.folgen}>
            {stand.folgen.map(f => <li key={f}>{f}</li>)}
          </ul>
          <label style={S.feld}>
            <span style={S.beschriftung}>Tippen Sie LÖSCHEN</span>
            <input style={S.eingabe} value={wort} onChange={e => setWort(e.target.value)} />
          </label>
          <label style={S.haken}>
            <input type="checkbox" checked={verstanden}
                   onChange={e => setVerstanden(e.target.checked)} />
            <span>Ich habe die Folgen gelesen und möchte die Löschung beantragen.</span>
          </label>
          <button style={S.knopfGefahrVoll} onClick={beantragen}
                  disabled={laeuft || wort.trim().toUpperCase() !== 'LÖSCHEN' || !verstanden}>
            {laeuft ? 'Wird aufgenommen …' : 'Löschung verbindlich beantragen'}
          </button>
        </div>
      )}
    </section>
  );
}

function farbe(h) {
  if (h.erfuellt === true) return 'var(--status-success-text)';
  if (h.erfuellt === false) return 'var(--status-warning-text)';
  return 'var(--text-45)';
}

function wort_fuer(h) {
  if (h.erfuellt === true) return 'erledigt';
  if (h.erfuellt === false) return 'steht entgegen';
  return h.ausraeumbar ? 'zu bedenken' : 'gilt und bleibt';
}

const S = {
  rahmen: { background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 8, padding: 22, marginTop: 28 },
  h2: { fontSize: 13, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', margin: '0 0 12px' },
  satz: { fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 16px', maxWidth: '64ch' },
  knoepfe: { display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', marginBottom: 18 },
  knopfRand: { fontWeight: 700, fontSize: 14, padding: '10px 18px', borderRadius: 6, border: '1px solid var(--brand-primary)', background: 'none', color: 'var(--brand-primary)', cursor: 'pointer' },
  knopfGefahr: { fontWeight: 700, fontSize: 14, padding: '10px 18px', borderRadius: 6, border: '1px solid var(--status-danger-text)', background: 'none', color: 'var(--status-danger-text)', cursor: 'pointer' },
  knopfGefahrVoll: { fontWeight: 900, fontSize: 14, padding: '13px 22px', borderRadius: 6, border: 'none', background: 'var(--error)', color: 'var(--text-on-danger)', cursor: 'pointer', marginTop: 14 },
  gesperrt: { fontSize: 13, color: 'var(--text-tertiary)', maxWidth: '46ch', lineHeight: 1.5 },
  beantragt: { fontSize: 13, color: 'var(--status-warning-text)', fontWeight: 700, maxWidth: '46ch', lineHeight: 1.5 },
  huerden: { listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 2 },
  huerde: { display: 'flex', gap: 12, alignItems: 'flex-start', padding: '12px 0', borderTop: '1px solid var(--border-light)' },
  punkt: { width: 8, height: 8, borderRadius: '50%', flex: 'none', marginTop: 7 },
  huerdeTitel: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', display: 'block' },
  huerdeStatus: { fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)', display: 'block', margin: '2px 0 4px' },
  huerdeText: { fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, display: 'block', maxWidth: '64ch' },
  frage: { marginTop: 18, paddingTop: 18, borderTop: '2px solid var(--status-danger-text)' },
  folgenKopf: { fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 8px' },
  folgen: { margin: '0 0 16px', paddingLeft: 20, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 },
  feld: { display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 280 },
  beschriftung: { fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' },
  eingabe: { padding: '10px 12px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 14, fontFamily: 'inherit' },
  haken: { display: 'flex', gap: 10, alignItems: 'flex-start', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: 14, maxWidth: '60ch' },
  fehler: { fontSize: 13, color: 'var(--status-danger-text)', margin: '0 0 12px' },
};
