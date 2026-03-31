import React, { useEffect, useState } from 'react';
import axios from 'axios';
import API_BASE_URL from '../config';
import AuditReport from './AuditReport';

const LEVEL_STYLES = {
  'Homepage Standard Platin': { color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { color: 'var(--brand-primary)', icon: '⛔' },
};

export default function AuditHistory({ leadId }) {
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);
  const [openAudit, setOpenAudit] = useState(null);
  const [loadingAuditId, setLoadingAuditId] = useState(null);

  const openFullReport = async (auditId) => {
    setLoadingAuditId(auditId);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/audit/${auditId}`);
      setOpenAudit(res.data);
    } catch (e) {
      alert('Audit konnte nicht geladen werden.');
    } finally {
      setLoadingAuditId(null);
    }
  };

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
    return <div className="skeleton" style={{ height: '60px' }} />;
  }

  if (audits.length === 0) {
    return (
      <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', padding: '12px 0' }}>
        Keine Audits vorhanden.
      </div>
    );
  }

  // Score improvement between first and last audit
  const improvement = audits.length >= 2
    ? audits[0].total_score - audits[audits.length - 1].total_score
    : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span  style={{ marginBottom: 0 }}>Audit-Historie</span>
        {improvement !== null && improvement !== 0 && (
          <span style={{
            fontSize: '11px', fontWeight: 700, fontFamily: 'var(--font-mono)',
            color: improvement > 0 ? 'var(--status-success-text)' : 'var(--brand-primary)',
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
              padding: '12px 16px',
              display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap',
            }}>
              {/* Date */}
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', minWidth: '80px' }}>
                {audit.created_at ? new Date(audit.created_at).toLocaleDateString('de-DE') : '—'}
              </span>
              {/* Level badge */}
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                padding: '2px 8px',
                borderRadius: 'var(--kc-radius-sm)',
                fontSize: '11px', fontWeight: 700, color: ls.color,
                background: `${ls.color}14`,
              }}>
                {ls.icon} {audit.level?.replace('Homepage Standard ', '')}
              </span>
              {/* Score */}
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '13px' }}>
                {audit.total_score}/100
              </span>
              {/* First issue preview */}
              {firstIssue && (
                <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  &ldquo;{firstIssue}&rdquo;
                </span>
              )}
              {/* Actions */}
              <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto', flexShrink: 0 }}>
                <button
                  className="kc-btn-ghost"
                  style={{ fontSize: '11px', padding: '2px 8px' }}
                  onClick={() => setExpanded(isOpen ? null : audit.id)}
                >
                  {isOpen ? 'Zuklappen' : 'Kurzinfo'}
                </button>
                <button
                  className="kc-btn-ghost"
                  style={{ fontSize: '11px', padding: '2px 8px', color: 'var(--kc-info, #2196f3)' }}
                  onClick={() => openFullReport(audit.id)}
                  disabled={loadingAuditId === audit.id}
                >
                  {loadingAuditId === audit.id ? '...' : 'Details anzeigen'}
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
                    background: downloadingId === audit.id ? '#ccc' : 'var(--text-primary)',
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
                padding: '16px',
                borderTop: '1px solid var(--border-light)',
                background: 'var(--bg-app)',
                fontSize: '13px',
                display: 'flex', flexDirection: 'column', gap: '12px',
              }}>
                {audit.ai_summary && (
                  <p style={{ color: 'var(--text-secondary)', lineHeight: 'var(--kc-leading-normal)', margin: 0 }}>
                    {audit.ai_summary}
                  </p>
                )}
                {audit.top_issues && audit.top_issues.length > 0 && (
                  <div>
                    <strong style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: 'var(--kc-tracking-wide)', color: 'var(--brand-primary)' }}>
                      Probleme
                    </strong>
                    <ul style={{ margin: '4px 0 0', paddingLeft: '16px' }}>
                      {audit.top_issues.map((issue, i) => (
                        <li key={i} style={{ color: 'var(--text-secondary)' }}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Full Audit Report Modal */}
      {openAudit && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', zIndex: 1000,
            overflowY: 'auto', padding: '20px',
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setOpenAudit(null); }}
        >
          <div style={{ maxWidth: 900, margin: '0 auto', borderRadius: 'var(--radius-lg)', overflow: 'hidden', background: 'var(--kc-weiss, #fff)' }}>
            <AuditReport
              auditData={openAudit}
              onClose={() => setOpenAudit(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
