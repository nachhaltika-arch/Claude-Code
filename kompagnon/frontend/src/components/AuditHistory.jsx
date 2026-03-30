import React, { useEffect, useState } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';

const LEVEL_STYLES = {
  'Homepage Standard Platin': { color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { color: 'var(--kc-rot)', icon: '⛔' },
};

export default function AuditHistory({ leadId }) {
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (!leadId) return;
    setLoading(true);
    axios
      .get(`${API_BASE_URL}/api/leads/${leadId}/audits`)
      .then((res) => setAudits(res.data))
      .catch(() => setAudits([]))
      .finally(() => setLoading(false));
  }, [leadId]);

  if (loading) {
    return <div className="kc-skeleton" style={{ height: '60px' }} />;
  }

  if (audits.length === 0) {
    return (
      <div style={{ fontSize: 'var(--kc-text-sm)', color: 'var(--kc-mittel)', padding: 'var(--kc-space-3) 0' }}>
        Keine Audits vorhanden.
      </div>
    );
  }

  // Score improvement between first and last audit
  const improvement = audits.length >= 2
    ? audits[0].total_score - audits[audits.length - 1].total_score
    : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-3)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="kc-eyebrow" style={{ marginBottom: 0 }}>Audit-Historie</span>
        {improvement !== null && improvement !== 0 && (
          <span style={{
            fontSize: 'var(--kc-text-xs)', fontWeight: 700, fontFamily: 'var(--kc-font-mono)',
            color: improvement > 0 ? 'var(--kc-success)' : 'var(--kc-rot)',
          }}>
            {audits[audits.length - 1].total_score} → {audits[0].total_score} Punkte
            ({improvement > 0 ? '+' : ''}{improvement})
            {improvement > 0 ? ' ↑ Verbesserung!' : ' ↓'}
          </span>
        )}
      </div>

      {audits.map((audit) => {
        const ls = LEVEL_STYLES[audit.level] || LEVEL_STYLES['Nicht konform'];
        const isOpen = expanded === audit.id;
        const firstIssue = audit.top_issues?.[0] || '';

        return (
          <div
            key={audit.id}
            className="kc-card"
            style={{ padding: 0, overflow: 'hidden' }}
          >
            {/* Row */}
            <div style={{
              padding: 'var(--kc-space-3) var(--kc-space-4)',
              display: 'flex', alignItems: 'center', gap: 'var(--kc-space-3)', flexWrap: 'wrap',
            }}>
              {/* Date */}
              <span style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-mittel)', fontFamily: 'var(--kc-font-mono)', minWidth: '80px' }}>
                {audit.created_at ? new Date(audit.created_at).toLocaleDateString('de-DE') : '—'}
              </span>
              {/* Level badge */}
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 'var(--kc-space-1)',
                padding: '2px var(--kc-space-2)',
                borderRadius: 'var(--kc-radius-sm)',
                fontSize: 'var(--kc-text-xs)', fontWeight: 700, color: ls.color,
                background: `${ls.color}14`,
              }}>
                {ls.icon} {audit.level?.replace('Homepage Standard ', '')}
              </span>
              {/* Score */}
              <span style={{ fontFamily: 'var(--kc-font-mono)', fontWeight: 700, fontSize: 'var(--kc-text-sm)' }}>
                {audit.total_score}/100
              </span>
              {/* First issue preview */}
              {firstIssue && (
                <span style={{ fontSize: 'var(--kc-text-xs)', color: 'var(--kc-text-subtil)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  &ldquo;{firstIssue}&rdquo;
                </span>
              )}
              {/* Actions */}
              <div style={{ display: 'flex', gap: 'var(--kc-space-2)', marginLeft: 'auto', flexShrink: 0 }}>
                <button
                  className="kc-btn-ghost"
                  style={{ fontSize: 'var(--kc-text-xs)', padding: '2px var(--kc-space-2)' }}
                  onClick={() => setExpanded(isOpen ? null : audit.id)}
                >
                  {isOpen ? 'Zuklappen' : 'Details'}
                </button>
                <button
                  onClick={() => {
                    (async () => {
                      try {
                        setDownloadingId(audit.id);
                        const response = await fetch(`${API_BASE_URL}/api/audit/${audit.id}/pdf`, { method: 'GET' });
                        if (!response.ok) {
                          const error = await response.json();
                          throw new Error(error.detail || 'PDF konnte nicht erstellt werden');
                        }
                        const blob = await response.blob();
                        if (blob.size === 0) throw new Error('PDF ist leer');
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `Homepage-Standard-Audit-${(audit.company_name || 'Audit').replace(/\s+/g, '-')}-${audit.id}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                      } catch (error) {
                        console.error('PDF Fehler:', error);
                        alert(`Fehler: ${error.message}`);
                      } finally {
                        setDownloadingId(null);
                      }
                    })();
                  }}
                  disabled={downloadingId === audit.id}
                  style={{
                    background: downloadingId === audit.id ? '#ccc' : '#0F1E3A',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    padding: '6px 12px',
                    fontSize: 12,
                    fontWeight: 700,
                    cursor: downloadingId === audit.id ? 'not-allowed' : 'pointer',
                  }}
                >
                  {downloadingId === audit.id ? '⏳ Erstellt...' : '📄 PDF'}
                </button>
              </div>
            </div>

            {/* Expanded detail */}
            {isOpen && (
              <div style={{
                padding: 'var(--kc-space-4)',
                borderTop: '1px solid var(--kc-rand)',
                background: 'var(--kc-hell)',
                fontSize: 'var(--kc-text-sm)',
                display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-3)',
              }}>
                {audit.ai_summary && (
                  <p style={{ color: 'var(--kc-text-sekundaer)', lineHeight: 'var(--kc-leading-normal)', margin: 0 }}>
                    {audit.ai_summary}
                  </p>
                )}
                {audit.top_issues && audit.top_issues.length > 0 && (
                  <div>
                    <strong style={{ fontSize: 'var(--kc-text-xs)', textTransform: 'uppercase', letterSpacing: 'var(--kc-tracking-wide)', color: 'var(--kc-rot)' }}>
                      Probleme
                    </strong>
                    <ul style={{ margin: 'var(--kc-space-1) 0 0', paddingLeft: 'var(--kc-space-4)' }}>
                      {audit.top_issues.map((issue, i) => (
                        <li key={i} style={{ color: 'var(--kc-text-sekundaer)' }}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
