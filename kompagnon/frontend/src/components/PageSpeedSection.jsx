import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

function scoreColor(score) {
  if (score === null || score === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
  if (score >= 90) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
  if (score >= 50) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
  return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
}

function vitalColor(key, raw) {
  if (raw === null || raw === undefined) return { bg: 'var(--status-neutral-bg)', text: 'var(--status-neutral-text)' };
  const thresholds = { lcp: [2500, 4000], cls: [0.1, 0.25], inp: [200, 500], fcp: [1800, 3000] };
  const [good, poor] = thresholds[key];
  if (raw < good) return { bg: 'var(--status-success-bg)', text: 'var(--status-success-text)' };
  if (raw < poor) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning-text)' };
  return { bg: 'var(--status-danger-bg)', text: 'var(--status-danger-text)' };
}

function fmtVital(key, raw) {
  if (raw === null || raw === undefined) return '—';
  if (key === 'cls') return raw.toFixed(3);
  return (raw / 1000).toFixed(2) + ' s';
}

function fmtTs(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
}

export default function PageSpeedSection({ leadId }) {
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [ps, setPs]               = useState(null);
  const [loading, setLoading]     = useState(true);
  const [measuring, setMeasuring] = useState(false);
  const [noUrl, setNoUrl]         = useState(false);
  const [error, setError]         = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/customers/${leadId}/pagespeed`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data && data.checked_at) setPs(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [leadId]); // eslint-disable-line

  const measure = async () => {
    setMeasuring(true); setError(null); setNoUrl(false);
    try {
      const res  = await fetch(`${API_BASE_URL}/api/customers/${leadId}/pagespeed`, { method: 'POST', headers });
      const data = await res.json();
      if (!res.ok) {
        if (data?.detail?.includes('Website-URL')) setNoUrl(true);
        else setError(data?.detail || 'Fehler bei der Messung');
      } else {
        setPs(data);
      }
    } catch { setError('Verbindungsfehler'); }
    setMeasuring(false);
  };

  const vitals = ps ? [
    { key: 'lcp', label: 'LCP', value: ps.lcp_mobile },
    { key: 'cls', label: 'CLS', value: ps.cls_mobile },
    { key: 'inp', label: 'INP', value: ps.inp_mobile },
    { key: 'fcp', label: 'FCP', value: ps.fcp_mobile },
  ] : [];

  return (
    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: isMobile ? '12px 16px' : '16px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>⚡</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Website-Performance</span>
        </div>
        <button
          onClick={measure} disabled={measuring}
          style={{ padding: '6px 14px', background: measuring ? 'var(--bg-elevated)' : 'var(--brand-primary)', color: measuring ? 'var(--text-tertiary)' : 'var(--text-inverse)', border: measuring ? '1px solid var(--border-medium)' : 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 600, cursor: measuring ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6, ...(isMobile ? { width: '100%', justifyContent: 'center' } : {}) }}
          onMouseEnter={e => { if (!measuring) e.currentTarget.style.opacity = '0.85'; }}
          onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
        >
          {measuring ? (<><span style={{ display: 'inline-block', width: 11, height: 11, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />Wird gemessen…</>) : 'PageSpeed messen'}
        </button>
      </div>

      {/* Body */}
      <div style={{ padding: isMobile ? '16px' : '20px' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
          </div>
        ) : noUrl ? (
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>Keine Website-URL hinterlegt — PageSpeed-Messung nicht möglich.</div>
        ) : error ? (
          <div style={{ fontSize: 12, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)', borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>{error}</div>
        ) : !ps ? (
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px 0' }}>Noch keine Messung vorhanden. Klicke auf „PageSpeed messen".</div>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12, marginBottom: 16 }}>
              {[{ label: 'Mobil', score: ps.mobile_score }, { label: 'Desktop', score: ps.desktop_score }].map(({ label, score }) => {
                const c = scoreColor(score);
                return (
                  <div key={label} style={{ background: c.bg, borderRadius: 'var(--radius-lg)', padding: '20px 16px', textAlign: 'center' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: c.text, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
                    <div style={{ fontSize: 42, fontWeight: 700, color: c.text, lineHeight: 1 }}>{score ?? '—'}</div>
                    <div style={{ fontSize: 11, color: c.text, marginTop: 4, opacity: 0.7 }}>/ 100</div>
                  </div>
                );
              })}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginBottom: 14 }}>
              {vitals.map(({ key, label, value }) => {
                const c = vitalColor(key, value);
                return (
                  <div key={key} style={{ background: c.bg, borderRadius: 'var(--radius-md)', padding: '12px 10px', textAlign: 'center' }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: c.text, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: c.text, lineHeight: 1.1 }}>{fmtVital(key, value)}</div>
                  </div>
                );
              })}
            </div>
            {ps.checked_at && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'right' }}>Zuletzt gemessen: {fmtTs(ps.checked_at)}</div>}
          </>
        )}
      </div>
    </div>
  );
}
