import { useState } from 'react';
import API_BASE_URL from '../config';

export default function KiReportPanel({ projectId, leadId, token }) {
  const [loading, setLoading] = useState(false);
  const [report, setReport]   = useState(null);
  const [error, setError]     = useState(null);
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  const generateReport = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/ki-report`, {
        method: 'POST',
        headers,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      const data = await res.json();
      setReport(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (score) => {
    if (score >= 80) return '#16a34a';
    if (score >= 50) return '#d97706';
    return '#dc2626';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            KI-Report aus Onboarding-Daten
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: 540 }}>
            Die KI analysiert alle vorhandenen Onboarding-Daten (Audit, Briefing,
            Crawler, Brand-Design, PageSpeed) und erstellt einen strukturierten Report
            mit Lückenanalyse für den Content-Schritt.
          </div>
        </div>
        <button
          onClick={generateReport}
          disabled={loading}
          style={{
            padding: '10px 22px', borderRadius: 8, border: 'none',
            background: loading ? '#94a3b8' : '#008eaa',
            color: 'white', fontSize: 13, fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap',
          }}
        >
          {loading ? (
            <>
              <span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />
              KI analysiert… (~30 Sek.)
            </>
          ) : 'Report jetzt erstellen'}
        </button>
      </div>

      {/* Fehler */}
      {error && (
        <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, fontSize: 13, color: '#dc2626' }}>
          {error}
        </div>
      )}

      {/* Platzhalter wenn noch kein Report */}
      {!report && !loading && !error && (
        <div style={{ padding: '48px 24px', background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 12, textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📊</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
            Noch kein Report vorhanden
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Klicke auf „Report jetzt erstellen" — die KI wertet alle Onboarding-Daten aus.
          </div>
        </div>
      )}

      {/* Report-Ausgabe */}
      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Vollständigkeits-Score */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
            {[
              { label: 'Vollständigkeit', value: `${report.completeness_score ?? '—'}%`, color: scoreColor(report.completeness_score ?? 0) },
              { label: 'Datenpunkte', value: report.data_points_count ?? '—', color: 'var(--text-primary)' },
              { label: 'Lücken', value: report.gaps_count ?? '—', color: report.gaps_count > 3 ? '#dc2626' : '#d97706' },
              { label: 'Bereit für Content', value: (report.completeness_score ?? 0) >= 60 ? 'Ja' : 'Nein', color: (report.completeness_score ?? 0) >= 60 ? '#16a34a' : '#dc2626' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: '14px 16px' }}>
                <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 24, fontWeight: 900, color }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Zusammenfassung */}
          {report.summary && (
            <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', marginBottom: 10 }}>Zusammenfassung</div>
              <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>{report.summary}</div>
            </div>
          )}

          {/* Vorhandene Daten */}
          {report.available_data && report.available_data.length > 0 && (
            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: '#16a34a', marginBottom: 10 }}>Vorhandene Daten</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {report.available_data.map((item, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, color: '#15803d' }}>
                    <span style={{ flexShrink: 0, marginTop: 2 }}>✓</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lücken */}
          {report.gaps && report.gaps.length > 0 && (
            <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: '#d97706', marginBottom: 10 }}>Fehlende Informationen (Lücken)</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {report.gaps.map((gap, i) => (
                  <div key={i} style={{ background: 'white', border: '1px solid #fed7aa', borderRadius: 8, padding: '10px 14px' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#92400e', marginBottom: 2 }}>{gap.field}</div>
                    <div style={{ fontSize: 12, color: '#b45309', lineHeight: 1.5 }}>{gap.impact}</div>
                    {gap.action && (
                      <div style={{ fontSize: 11, color: '#d97706', marginTop: 4, fontStyle: 'italic' }}>{gap.action}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empfehlung */}
          {report.recommendation && (
            <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: '16px 20px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', marginBottom: 8 }}>Empfehlung</div>
              <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.65 }}>{report.recommendation}</div>
            </div>
          )}

          {/* Vollständige Rohdaten für Content-KI */}
          {report.content_brief && (
            <details style={{ background: 'var(--bg-app)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: '12px 16px' }}>
              <summary style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                Content-Brief (für KI-Texterstellung)
              </summary>
              <pre style={{ marginTop: 12, fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.6, fontFamily: 'monospace' }}>
                {typeof report.content_brief === 'string' ? report.content_brief : JSON.stringify(report.content_brief, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
