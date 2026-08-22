/**
 * Briefing und Analyse als Schritt-Einbettung.
 *
 * **Warum eigene Datei (L-25, 22.08.2026).** `ProzessFlow.jsx` hatte 2.307
 * Zeilen. 493 davon waren tot — `PHASEN`, `ALLE_SCHRITTE` und die
 * Standardkomponente, die niemand importierte. Der Rest bestand aus einem
 * Verteiler (`SchrittInhalt`) und siebzehn Einbettungen, die je einen
 * Schritt des Online-Editors anzeigen.
 *
 * Geschnitten ist nach **Thema**, nicht nach Groesse: Die Einbettungen
 * teilen untereinander nichts ausser den Bibliotheks-Importen — nachgemessen
 * vor dem Schnitt. `SchrittInhalt` bleibt in `ProzessFlow.jsx` und holt sie
 * von hier.
 */
import { useAudit } from '../../hooks/useAudit';
import AuditReport from '../AuditReport';
import BriefingWizard from '../BriefingWizard';
import { useEffect, useState } from 'react';


export function BriefingUnternehmenEmbed({ lead, localBriefing, reloadBriefing }) {
  const [editing, setEditing] = useState(false);
  const b = localBriefing;
  const hasDaten = !!(b?.gewerk || b?.leistungen || b?.usp);

  if (editing || !hasDaten) {
    return (
      <div style={{ padding: '20px 24px' }}>
        {hasDaten && (
          <button onClick={() => setEditing(false)}
            style={{ marginBottom: 12, padding: '5px 14px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            Zurueck zur Uebersicht
          </button>
        )}
        <BriefingWizard
          leadId={lead.id}
          leadData={localBriefing}
          onClose={() => { if (hasDaten) setEditing(false); }}
          onComplete={() => { reloadBriefing(); setEditing(false); }}
          embedded
        />
      </div>
    );
  }

  const rows = [
    b.gewerk        && { label: 'Gewerk / Branche', value: b.gewerk },
    b.wz_title      && { label: 'WZ-Code',          value: `${b.wz_code} — ${b.wz_title}` },
    b.leistungen    && { label: 'Leistungen',        value: b.leistungen },
    b.einzugsgebiet && { label: 'Einzugsgebiet',     value: b.einzugsgebiet },
    b.usp           && { label: 'USP',               value: b.usp },
    b.zielgruppe    && { label: 'Zielgruppe',        value: typeof b.zielgruppe === 'string' ? b.zielgruppe : b.zielgruppe?.primaer || '' },
    b.farben        && { label: 'Farben',            value: b.farben },
    b.stil          && { label: 'Stil',              value: b.stil },
    b.mitbewerber   && { label: 'Mitbewerber',       value: b.mitbewerber },
    b.vorbilder     && { label: 'Vorbilder',         value: b.vorbilder },
    b.sonstige_hinweise && { label: 'Hinweise',      value: b.sonstige_hinweise },
  ].filter(Boolean);

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Briefing-Daten</div>
        <button onClick={() => setEditing(true)}
          style={{ padding: '6px 16px', borderRadius: 6, border: '1px solid var(--brand-primary-mid)', background: 'transparent', color: 'var(--brand-primary-mid)', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          Bearbeiten
        </button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 20px' }}>
        {rows.map(({ label, value }) => (
          <div key={label}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.5, whiteSpace: 'pre-line' }}>{value}</div>
          </div>
        ))}
      </div>
      {(b.logo_vorhanden || b.fotos_vorhanden) && (
        <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
          {b.logo_vorhanden && <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 99, background: '#dcfce7', color: '#059669', fontWeight: 600 }}>Logo vorhanden</span>}
          {b.fotos_vorhanden && <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 99, background: '#dcfce7', color: '#059669', fontWeight: 600 }}>Fotos vorhanden</span>}
        </div>
      )}
    </div>
  );
}


export function AuditEmbed({ project, lead, headers, latestAudit, onAuditComplete }) {
  const websiteUrl = lead?.website_url || project?.website_url;
  const { phase, result, progress, error, start, reset } = useAudit({
    leadId:      project?.lead_id,
    websiteUrl,
    companyName: lead?.company_name || project?.company_name || '',
    city:        lead?.city  || '',
    headers,
    autoStart:      true,
    existingResult: latestAudit,
  });

  useEffect(() => {
    if (phase === 'done' && result && onAuditComplete) onAuditComplete(result);
  }, [phase, result]); // eslint-disable-line

  return (
    <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      {websiteUrl && (
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--text-tertiary)' }}>URL: </span>
          <a href={websiteUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-primary-mid)', textDecoration: 'none' }}>{websiteUrl}</a>
        </div>
      )}

      {phase === 'running' && <AuditRunningUI progress={progress} />}
      {phase === 'error'   && <AuditErrorUI   error={error} onRetry={start} />}
      {phase === 'done' && result && <AuditReport auditData={result} />}

      {phase === 'idle' && !websiteUrl && (
        <span style={{ fontSize: 12, color: 'var(--status-warning-text)' }}>Keine Website-URL hinterlegt</span>
      )}
      {phase === 'idle' && !result && (
        <div style={{ textAlign: 'center', padding: '32px 20px', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 36, marginBottom: 10 }}>🔍</div>
          <div style={{ fontSize: 13 }}>Noch kein Audit vorhanden. Klicke auf Audit starten.</div>
        </div>
      )}

      {phase !== 'running' && (
        <button
          onClick={phase === 'done' ? reset : start}
          disabled={!websiteUrl}
          style={{ alignSelf: 'flex-start', padding: '10px 22px', borderRadius: 8, border: 'none', background: !websiteUrl ? 'var(--border-medium)' : 'var(--kc-dark)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: !websiteUrl ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', textTransform: 'uppercase' }}
        >
          {phase === 'done' ? 'Neuen Audit starten' : 'Audit starten'}
        </button>
      )}
    </div>
  );
}


// Nur hier drin gebraucht (Zeile ~895). Das `export` davor nutzte
// niemand — ein Export, den keiner holt, behauptet eine Schnittstelle,
// die es nicht gibt (L-25, 22.08.2026).
export function AuditRunningUI({ progress }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, background: 'var(--info-bg, #EFF6FF)', borderRadius: 8, padding: '16px 20px' }}>
      <span style={{ width: 32, height: 32, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--kc-mid)', animation: 'spin 0.8s linear infinite', flexShrink: 0, display: 'inline-block' }} />
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Audit läuft…</div>
        {progress && <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{progress}</div>}
      </div>
    </div>
  );
}


export function AuditErrorUI({ error, onRetry }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--error-bg, #FEF2F2)', border: '1px solid rgba(192,57,43,0.2)', borderRadius: 8, padding: '14px 18px' }}>
      <span style={{ fontSize: 20, flexShrink: 0 }}>⚠️</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--error, #C0392B)' }}>Audit fehlgeschlagen</div>
        {error && <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 3 }}>{error}</div>}
      </div>
      {onRetry && (
        <button onClick={onRetry} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: 'var(--kc-dark)', color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
          Erneut versuchen
        </button>
      )}
    </div>
  );
}

