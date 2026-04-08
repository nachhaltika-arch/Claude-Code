import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';

export default function NewsletterAnalytics({ campaignId, onClose }) {
  const { token } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!campaignId) return;
    const mkH = () => ({
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    });
    fetch(`${API_BASE_URL}/api/newsletter/campaigns/${campaignId}/stats`, { headers: mkH() })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => setStats(d))
      .catch(() => toast.error('Statistiken konnten nicht geladen werden'))
      .finally(() => setLoading(false));
  }, [campaignId, token]);

  // ── Derived values ──────────────────────────────────────────────

  const openPct = stats?.openRate != null ? stats.openRate * 100 : null;
  const clickPct = stats?.clickRate != null ? stats.clickRate * 100 : null;

  const ratingBadge = () => {
    if (openPct == null) return null;
    if (openPct > 25) return { label: 'Sehr gute Oeffnungsrate', bg: 'var(--status-success-bg)', color: 'var(--status-success-text)', icon: ' \u2713' };
    if (openPct >= 15) return { label: 'Durchschnittliche Oeffnungsrate', bg: 'var(--status-warning-bg)', color: '#92600a', icon: '' };
    return { label: 'Oeffnungsrate verbessern', bg: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', icon: '' };
  };
  const rating = ratingBadge();

  // ── Styles ──────────────────────────────────────────────────────

  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: 'var(--bg-surface)', borderRadius: 12, padding: 28, width: '100%', maxWidth: 520, display: 'flex', flexDirection: 'column', gap: 20 };
  const card = { background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', padding: '16px 18px' };
  const btnPrimary = { background: 'var(--brand-primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const btnSecondary = { background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', padding: '8px 16px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };

  const ProgressBar = ({ pct, color = '#008eaa' }) => (
    <div style={{ height: 6, borderRadius: 3, background: 'var(--bg-app)', marginTop: 8, overflow: 'hidden' }}>
      <div style={{ height: '100%', borderRadius: 3, background: color, width: `${Math.min(pct ?? 0, 100)}%`, transition: 'width 0.4s ease' }} />
    </div>
  );

  return (
    <div style={overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={modal}>
        <h3 style={{ fontSize: 17, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Kampagnen-Statistiken</h3>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 120, color: 'var(--text-tertiary)', fontSize: 13 }}>
            <svg width="20" height="20" viewBox="0 0 20 20" style={{ animation: 'spin 1s linear infinite', marginRight: 8 }}>
              <circle cx="10" cy="10" r="8" fill="none" stroke="var(--border-light)" strokeWidth="2.5" />
              <circle cx="10" cy="10" r="8" fill="none" stroke="var(--brand-primary)" strokeWidth="2.5" strokeDasharray="32 50" strokeLinecap="round" />
            </svg>
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            Statistiken werden geladen...
          </div>
        ) : stats ? (
          <>
            {/* ── 4 Stat tiles ─────────────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {/* Open rate */}
              <div style={card}>
                <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Oeffnungsrate</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--brand-primary)', marginTop: 4 }}>
                  {openPct != null ? `${openPct.toFixed(1)}%` : '-'}
                </div>
                <ProgressBar pct={openPct} />
              </div>

              {/* Click rate */}
              <div style={card}>
                <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Klickrate</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--brand-primary)', marginTop: 4 }}>
                  {clickPct != null ? `${clickPct.toFixed(1)}%` : '-'}
                </div>
                <ProgressBar pct={clickPct} />
              </div>

              {/* Unsubscriptions */}
              <div style={card}>
                <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Abmeldungen</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                  {stats.unsubscriptions ?? '-'}
                </div>
              </div>

              {/* Sent count */}
              <div style={card}>
                <div style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Versendet an</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                  {stats.sentCount ?? '-'}
                </div>
              </div>
            </div>

            {/* ── Rating badge ─────────────────────────────────────── */}
            {rating && (
              <div style={{
                display: 'inline-flex', alignItems: 'center', alignSelf: 'flex-start',
                padding: '6px 14px', borderRadius: 999,
                background: rating.bg, color: rating.color,
                fontSize: 13, fontWeight: 500,
              }}>
                {rating.label}{rating.icon}
              </div>
            )}

            {/* ── Explanation box ──────────────────────────────────── */}
            <div style={{
              background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '14px 18px',
              fontSize: 12, lineHeight: 1.6, color: 'var(--text-secondary)',
            }}>
              <strong>Oeffnungsrate:</strong> Anteil der Empfaenger, die die E-Mail geoeffnet haben.<br />
              <strong>Klickrate:</strong> Anteil, die auf mindestens einen Link geklickt haben.
            </div>
          </>
        ) : (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
            Keine Statistiken verfuegbar.
          </div>
        )}

        {/* ── Buttons ──────────────────────────────────────────────── */}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button style={btnSecondary} onClick={onClose}>Schliessen</button>
          <button style={btnPrimary} onClick={() => window.print()}>Als PDF drucken</button>
        </div>
      </div>
    </div>
  );
}
