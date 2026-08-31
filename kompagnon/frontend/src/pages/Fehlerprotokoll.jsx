import React, { useEffect, useState } from 'react';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';

/**
 * Was der Server nicht verarbeiten konnte.
 *
 * Lücke L-10: Produktiv gab es keine Fehlerauskunft. Der 500er beim Anlegen
 * einer Lektion stand monatelang, ohne dass ihn jemand sah — die Oberfläche
 * verschluckte ihn, und ins Serverlog sieht niemand täglich.
 *
 * Gleiche Fehler an derselben Stelle stehen einmal, mit Zähler. Sonst wäre
 * die Liste nach einem kaputten Endpunkt unlesbar — und eine unlesbare Liste
 * ist so gut wie keine.
 */
export default function Fehlerprotokoll() {
  const { token } = useAuth();
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');
  const [offen, setOffen] = useState(null);

  const kopf = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    let abgebrochen = false;
    fetch(`${API_BASE_URL}/api/fehler/`, { headers: kopf })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(d => { if (!abgebrochen) setDaten(d); })
      .catch(e => { if (!abgebrochen) setFehler(`Liste nicht ladbar: ${e.message}`); });
    return () => { abgebrochen = true; };
  }, []); // eslint-disable-line

  const spurLaden = async (id) => {
    if (offen?.id === id) { setOffen(null); return; }
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/fehler/${id}`, { headers: kopf });
      if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`);
      setOffen(await antwort.json());
    } catch (e) {
      setFehler(`Spur nicht ladbar: ${e.message}`);
    }
  };

  const zeit = (wert) => (wert ? new Date(wert).toLocaleString('de-DE') : '—');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
          Fehlerprotokoll
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
          {daten
            ? `${daten.letzte_24h} in den letzten 24 Stunden · ${daten.gesamt} insgesamt`
            : 'wird geladen…'}
        </p>
      </div>

      {fehler && (
        <div role="alert" style={{
          padding: '10px 14px', background: 'var(--status-danger-bg)',
          color: 'var(--status-danger-text)', border: '1px solid var(--status-danger-text)',
          borderRadius: 'var(--radius-md)', fontSize: 13,
        }}>{fehler}</div>
      )}

      {daten && daten.eintraege.length === 0 && (
        <div style={{
          padding: 32, textAlign: 'center', color: 'var(--text-secondary)',
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', fontSize: 14,
        }}>
          Nichts vorgefallen. Das ist die richtige Antwort, nicht die leere Seite.
        </div>
      )}

      {daten && daten.eintraege.map(e => (
        <div key={e.id} style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', padding: '12px 16px',
        }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 700, color: 'var(--status-danger-text)', fontSize: 14 }}>
              {e.art}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
              {e.methode} {e.pfad}
            </span>
            {e.anzahl > 1 && (
              <span style={{
                fontSize: 12, fontWeight: 700, padding: '1px 8px', borderRadius: 99,
                background: 'var(--status-warning-bg)', color: 'var(--status-warning-text)',
              }}>{e.anzahl}×</span>
            )}
          </div>

          <div style={{ fontSize: 13, color: 'var(--text-primary)', marginTop: 6 }}>
            {e.meldung || '(ohne Meldung)'}
          </div>

          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6 }}>
            zuletzt {zeit(e.zuletzt)} · zuerst {zeit(e.zuerst)}
          </div>

          <button
            type="button" onClick={() => spurLaden(e.id)}
            style={{
              marginTop: 8, background: 'none', border: 'none', padding: 0,
              color: 'var(--text-brand)', fontSize: 12, cursor: 'pointer',
              fontFamily: 'var(--font-sans)', textDecoration: 'underline',
            }}
          >{offen?.id === e.id ? 'Spur ausblenden' : 'Spur anzeigen'}</button>

          {offen?.id === e.id && (
            <pre style={{
              marginTop: 8, padding: 12, overflowX: 'auto',
              background: 'var(--bg-app)', border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-md)', fontSize: 12, lineHeight: 1.5,
              color: 'var(--text-secondary)', whiteSpace: 'pre-wrap',
            }}>{offen.spur || '(keine Spur aufbewahrt)'}</pre>
          )}
        </div>
      ))}
    </div>
  );
}
