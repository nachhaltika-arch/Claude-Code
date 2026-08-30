/**
 * Die Auditgeschichte eines Betriebs (L-25).
 *
 * Am 2026-08-30 aus `CustomerDetail.jsx` herausgeloest — 252 der damals 2.512
 * Zeilen. Sie war dort schon eine eigene Funktion.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import API_BASE_URL from '../../config';
import { useScreenSize } from '../../utils/responsive';
import { fmtTs } from './formate';

export default function AuditHistorySection({ customerId, customer, headers }) {
  const { isMobile } = useScreenSize();
  const [audits, setAudits]           = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [starting, setStarting]       = useState(false);
  const [startError, setStartError]   = useState(null);
  const [pollingId, setPollingId]     = useState(null); // audit id being polled
  const pollRef                       = useRef(null);

  const fetchAudits = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/audit/lead/${customerId}`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAudits(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e) {
      console.error('[CustomerDetail] fetchAudits failed:', e);
      setError(`Audit-Historie konnte nicht geladen werden: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [customerId]); // eslint-disable-line

  // SCHRITT 3 — customerId als Abhängigkeit
  useEffect(() => {
    setLoading(true);
    fetchAudits();
  }, [customerId]); // eslint-disable-line

  // Cleanup polling on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    setPollingId(null);
  };

  // SCHRITT 2 — Polling nach Audit-Start
  const startPolling = (auditId) => {
    setPollingId(auditId);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/audit/${auditId}`, { headers });
        if (!res.ok) { stopPolling(); return; }
        const data = await res.json();
        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling();
          fetchAudits();
        }
      } catch (e) {
        console.error('[CustomerDetail] polling error:', e);
        stopPolling();
      }
    }, 3000);
  };

  const handleStartAudit = async () => {
    const websiteUrl = customer?.website_url || customer?.url || customer?.domain;
    if (!websiteUrl) {
      setStartError('Keine Website-URL beim Kunden hinterlegt.');
      return;
    }
    setStarting(true);
    setStartError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/audit/start`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          website_url: websiteUrl,
          company_name: customer?.company_name || '',
          contact_name: customer?.contact_name || '',
          lead_id: Number(customerId),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStartError(data?.detail || 'Audit konnte nicht gestartet werden.');
      } else {
        // Optimistically add a pending row, then poll for completion
        setAudits(prev => [{ id: data.id, status: 'pending', website_url: websiteUrl, created_at: new Date().toISOString() }, ...prev]);
        startPolling(data.id);
      }
    } catch (e) {
      console.error('[CustomerDetail] startAudit failed:', e);
      setStartError(`Verbindungsfehler: ${e.message}`);
    }
    setStarting(false);
  };

  const scoreLabel = (score) => {
    if (score === null || score === undefined) return '—';
    return `${score}/100`;
  };

  const scoreColors = (score) => {
    if (score === null || score === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
    if (score >= 70) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
    if (score >= 45) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
    return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
  };

  const statusBadge = (status, auditId) => {
    const isPolling = pollingId === auditId;
    const map = {
      completed: { label: 'Abgeschlossen', bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
      failed:    { label: 'Fehlgeschlagen', bg: 'var(--status-danger-bg)',  color: 'var(--status-danger-text)' },
      pending:   { label: isPolling ? 'Läuft…' : 'Ausstehend', bg: 'var(--status-info-bg)', color: 'var(--status-info-text)' },
      running:   { label: 'Läuft…', bg: 'var(--status-info-bg)', color: 'var(--status-info-text)' },
    };
    const s = map[status] || map.pending;
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        background: s.bg, color: s.color,
        borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px',
      }}>
        {(status === 'pending' || status === 'running') && (
          <span style={{ width: 7, height: 7, borderRadius: '50%', border: '1.5px solid currentColor', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite', display: 'inline-block', flexShrink: 0 }} />
        )}
        {s.label}
      </span>
    );
  };

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{
        padding: isMobile ? '12px 16px' : '16px 20px',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'stretch' : 'center',
        justifyContent: 'space-between',
        gap: isMobile ? 10 : 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>🔍</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Audit-Historie</span>
          {!loading && audits.length > 0 && (
            <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary-mid)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>
              {audits.length}
            </span>
          )}
        </div>
        <button
          onClick={handleStartAudit}
          disabled={starting || !!pollingId}
          style={{
            padding: '8px 14px',
            background: (starting || pollingId) ? 'var(--bg-elevated)' : 'var(--brand-primary)',
            color: (starting || pollingId) ? 'var(--text-tertiary)' : 'var(--text-inverse)',
            border: (starting || pollingId) ? '1px solid var(--border-medium)' : 'none',
            borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600,
            cursor: (starting || pollingId) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            ...(isMobile ? { width: '100%' } : {}),
          }}
        >
          {(starting || pollingId) ? (
            <>
              <span style={{ width: 11, height: 11, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block', flexShrink: 0 }} />
              {starting ? 'Wird gestartet…' : 'Audit läuft…'}
            </>
          ) : '+ Audit starten'}
        </button>
      </div>

      {/* Error banner */}
      {startError && (
        <div style={{ margin: '12px 20px 0', padding: '10px 14px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
          {startError}
        </div>
      )}

      {/* Body */}
      <div style={{ padding: '4px 0' }}>
        {loading ? (
          <div style={{ padding: '32px 20px', display: 'flex', justifyContent: 'center' }}>
            <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : error ? (
          <div style={{ margin: '12px 20px', padding: '10px 14px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
            {error}
          </div>
        ) : audits.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.3 }}>🔍</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Noch kein Audit durchgeführt</div>
            <div style={{ fontSize: 12 }}>Klicke auf „+ Audit starten" um eine Website-Analyse zu starten.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            {/* Table header */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 100px 90px 120px',
              minWidth: 460, gap: 12, padding: '8px 20px',
              fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
              textTransform: 'uppercase', letterSpacing: '0.06em',
              borderBottom: '1px solid var(--border-light)',
            }}>
              <span>Website</span><span>Score</span><span>Status</span><span>Datum</span>
            </div>

            {audits.map(audit => {
              const c = scoreColors(audit.total_score);
              return (
                <div
                  key={audit.id}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr 100px 90px 120px',
                    minWidth: 460, gap: 12, padding: '12px 20px',
                    alignItems: 'center', borderBottom: '1px solid var(--border-light)',
                    transition: 'background var(--transition-fast)',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {audit.website_url}
                    {audit.company_name && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{audit.company_name}</div>
                    )}
                  </div>
                  <div>
                    {audit.status === 'completed' ? (
                      <span style={{ display: 'inline-block', padding: '2px 8px', background: c.bg, color: c.text, borderRadius: 'var(--radius-full)', fontSize: 12, fontWeight: 700 }}>
                        {scoreLabel(audit.total_score)}
                      </span>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                    )}
                  </div>
                  <div>{statusBadge(audit.status, audit.id)}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{fmtTs(audit.created_at)}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── helpers ───────────────────────────────────────────────────

