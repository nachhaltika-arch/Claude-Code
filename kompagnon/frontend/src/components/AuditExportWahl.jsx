/**
 * Welches Audit exportiert werden soll (BUCH-12, FIX-3 — L-115).
 *
 * **Der Anlass.** In `MassExport` trugen alle sechs Kacheln „Bald verfügbar",
 * und zwei davon gab es längst: `/api/audit/{id}/pdf` und
 * `/api/audit/{id}/angebot`, beide produktiv im Auditwerkzeug im Einsatz. Eine
 * Funktion nicht anzubieten, die man hat, ist verschenkter Nutzen — und lässt
 * das Werkzeug unfertiger wirken, als es ist.
 *
 * **Warum es eine Auswahl braucht.** Beide Endpunkte brauchen ein Audit. Die
 * Seite heißt „Massen-Export" und kennt keins; die Kachel einfach zu
 * verdrahten hätte einen Knopf ergeben, der nicht weiß, worüber er berichtet.
 *
 * **Die Kopfzeile geht mit.** Beide Adressen stehen hinter
 * `require_innendienst`. Ohne sie käme eine 401 zurück, und der Nutzer sähe
 * einen Download, der leer ist — der unangenehmste Fehler, weil er wie ein
 * kaputtes PDF aussieht und nicht wie eine fehlende Anmeldung.
 */
import React, { useEffect, useState } from 'react';
import API_BASE_URL from '../config';

/** Wie viele Audits zur Auswahl stehen. Mehr wäre eine Suche, keine Liste. */
export const HOECHSTENS = 25;

const BESCHRIFTUNG = {
  pdf: { titel: 'Audit-Bericht als PDF', pfad: 'pdf', datei: 'Audit-Bericht' },
  angebot: { titel: 'Angebot als PDF', pfad: 'angebot', datei: 'Angebot' },
};

function datum(roh) {
  if (!roh) return '';
  const d = new Date(roh);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('de-DE');
}

export default function AuditExportWahl({ art, kopfzeilen, onSchliessen }) {
  const { titel, pfad, datei } = BESCHRIFTUNG[art] || BESCHRIFTUNG.pdf;

  const [audits, setAudits] = useState(null);   // `null` = wird noch geladen
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(0);

  useEffect(() => {
    let abgebrochen = false;

    fetch(`${API_BASE_URL}/api/audit/recent?limit=${HOECHSTENS}`,
          { headers: kopfzeilen })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('Abruf'))))
      .then((d) => {
        if (abgebrochen) return;
        setAudits(Array.isArray(d) ? d : []);
      })
      .catch(() => {
        if (!abgebrochen) {
          setAudits([]);
          setFehler('Die Audits konnten nicht geladen werden.');
        }
      });

    return () => { abgebrochen = true; };
  }, [kopfzeilen]);

  const holen = async (audit) => {
    setFehler('');
    setLaeuft(audit.id);
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/audit/${audit.id}/${pfad}`,
        { headers: kopfzeilen });
      if (!antwort.ok) throw new Error(`HTTP ${antwort.status}`);

      const blob = await antwort.blob();
      const adresse = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = adresse;
      a.download = `${datei}-${audit.company_name || audit.id}.pdf`
        .replace(/[^\w.\-äöüÄÖÜß]+/g, '-');
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(adresse);
      onSchliessen();
    } catch {
      // Ein Knopf, der nichts tut, ist schlimmer als einer mit Fehlermeldung.
      setFehler('Der Export ist fehlgeschlagen. Bitte erneut versuchen.');
    } finally {
      setLaeuft(0);
    }
  };

  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-lg)', padding: 20, marginTop: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0,
                     color: 'var(--text-primary)' }}>{titel}</h2>
        <button type="button" onClick={onSchliessen} aria-label="Schließen"
                style={{ background: 'var(--bg-app)', border: 'none',
                         borderRadius: 8, width: 32, height: 32,
                         cursor: 'pointer', fontSize: 16 }}>×</button>
      </div>

      {fehler && (
        <div role="alert" style={{
          background: 'var(--status-danger-bg)',
          color: 'var(--status-danger-text)', borderRadius: 8,
          padding: '10px 12px', fontSize: 13, marginBottom: 12,
        }}>{fehler}</div>
      )}

      {audits === null && (
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Einen Moment…
        </p>
      )}

      {audits !== null && audits.length === 0 && !fehler && (
        // Nicht eine leere Liste: Die sieht aus wie ein Ladefehler.
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Es gibt noch kein abgeschlossenes Audit. Starten Sie eines im
          Auditwerkzeug — danach steht es hier zum Export bereit.
        </p>
      )}

      {audits !== null && audits.length > 0 && (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0,
                     display: 'flex', flexDirection: 'column', gap: 6 }}>
          {audits.map((a) => (
            <li key={a.id}>
              <button
                type="button"
                onClick={() => holen(a)}
                disabled={laeuft === a.id}
                style={{
                  width: '100%', textAlign: 'left', background: 'var(--bg-app)',
                  border: '1px solid var(--border-light)', borderRadius: 8,
                  padding: '10px 12px', cursor: 'pointer', minHeight: 44,
                  fontSize: 13, color: 'var(--text-primary)',
                }}
              >
                <span style={{ fontWeight: 700 }}>
                  {a.company_name || a.website_url || `Audit ${a.id}`}
                </span>
                <span style={{ color: 'var(--text-tertiary)' }}>
                  {' · '}{a.total_score} Punkte
                  {datum(a.created_at) ? ` · ${datum(a.created_at)}` : ''}
                  {laeuft === a.id ? ' · wird erzeugt…' : ''}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
