import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import API_BASE_URL from '../config';
import AuditReport from './AuditReport';
import { useScreenSize } from '../utils/responsive';

const LEVEL_STYLES = {
  'Homepage Standard Platin': { color: '#283593', icon: '\uD83C\uDFC6' },
  'Homepage Standard Gold':   { color: '#f57f17', icon: '\uD83E\uDD47' },
  'Homepage Standard Silber': { color: '#616161', icon: '\uD83E\uDD48' },
  'Homepage Standard Bronze': { color: '#4e342e', icon: '\uD83E\uDD49' },
  'Nicht konform':            { color: 'var(--brand-primary)', icon: '⛔' },
};

export default function AuditHistory({ leadId }) {
  const { isMobile } = useScreenSize();
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

  const downloadPdf = async (audit) => {
    try {
      setDownloadingId(audit.id);
      const response = await fetch(`${API_BASE_URL}/api/audit/${audit.id}/pdf`);
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'PDF konnte nicht erstellt werden');
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
                  onClick={() => downloadPdf(audit)}
                  disabled={downloadingId === audit.id}
                  style={{
                    background: downloadingId === audit.id ? 'var(--bg-elevated)' : 'var(--text-primary)',
                    color: downloadingId === audit.id ? 'var(--text-tertiary)' : 'var(--text-inverse)',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    padding: '6px 12px',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: downloadingId === audit.id ? 'not-allowed' : 'pointer',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {downloadingId === audit.id ? '⏳ Erstellt…' : '📄 PDF'}
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

      {/* Full Audit Report Modal — rendered via portal to bypass transform stacking context */}
      {openAudit && createPortal(
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.75)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'stretch',
            justifyContent: 'center',
            padding: 0,
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setOpenAudit(null); }}
        >
          {/* Inner container — full height, max 960px wide */}
          <div style={{
            width: '100%',
            maxWidth: isMobile ? '100%' : 960,
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-surface)',
            borderRadius: 0,
            overflow: 'hidden',
          }}>
            {/* Fixed header bar — 52px */}
            <div style={{
              flexShrink: 0,
              height: 52,
              background: 'var(--bg-surface)',
              borderBottom: '0.5px solid var(--border-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 20px',
              gap: 12,
            }}>
              {/* Left — company name + score */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                <span style={{
                  fontSize: 14, fontWeight: 600, color: 'var(--text-primary)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {openAudit.company_name || openAudit.website_url}
                </span>
                {openAudit.total_score != null && (() => {
                  const s = openAudit.total_score;
                  const bg  = s >= 70 ? 'var(--status-success-bg)'  : s >= 45 ? 'var(--status-warning-bg)'  : 'var(--status-danger-bg)';
                  const col = s >= 70 ? 'var(--status-success-text)' : s >= 45 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';
                  return (
                    <span style={{ flexShrink: 0, background: bg, color: col, borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 700, padding: '2px 8px' }}>
                      {s}/100
                    </span>
                  );
                })()}
              </div>

              {/* Right — PDF + Close */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                <button
                  onClick={() => downloadPdf(openAudit)}
                  disabled={downloadingId === openAudit.id}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    background: 'transparent',
                    border: '0.5px solid var(--border-medium)',
                    color: 'var(--text-secondary)',
                    borderRadius: 'var(--radius-md)',
                    padding: '5px 12px', fontSize: 12, fontWeight: 500,
                    cursor: downloadingId === openAudit.id ? 'not-allowed' : 'pointer',
                    fontFamily: 'var(--font-sans)',
                    opacity: downloadingId === openAudit.id ? 0.5 : 1,
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {downloadingId === openAudit.id ? '⏳ Erstellt…' : '📄 PDF'}
                </button>
                <button
                  onClick={() => setOpenAudit(null)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    background: 'transparent',
                    border: '0.5px solid var(--border-medium)',
                    color: 'var(--text-secondary)',
                    borderRadius: 'var(--radius-md)',
                    padding: '5px 12px', fontSize: 12, fontWeight: 500,
                    cursor: 'pointer', fontFamily: 'var(--font-sans)',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  ✕ Schließen
                </button>
              </div>
            </div>

            {/* Scrollable report area */}
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {/* onClose not passed — suppresses AuditReport's own floating × */}
              <AuditReport auditData={openAudit} />
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
