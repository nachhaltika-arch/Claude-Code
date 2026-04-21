import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const SOURCES = [
  { key: 'facebook',  label: 'Facebook',    color: '#1877F2', icon: 'f' },
  { key: 'linkedin',  label: 'LinkedIn',    color: '#0A66C2', icon: 'in' },
  { key: 'google',    label: 'Google Ads',  color: '#EA4335', icon: 'G' },
  { key: 'postkarte', label: 'Postkarte',   color: '#008eaa', icon: 'QR' },
  { key: 'telefon',   label: 'KI-Telefon',  color: '#1D9E75', icon: 'T' },
];

const GUIDES = [
  { key: 'facebook',  text: 'Gehe zu Meta Business Suite → Lead Ads → Einstellungen → Webhook URL eintragen. Als URL die oben angezeigte Webhook-URL verwenden.' },
  { key: 'linkedin',  text: 'Gehe zu LinkedIn Campaign Manager → Lead Gen Forms → Einstellungen → Webhook URL eintragen.' },
  { key: 'google',    text: 'Google Ads → Lead Form Extensions → Webhook Integration → URL eintragen.' },
  { key: 'postkarte', text: 'QR-Code auf der Postkarte zeigt auf die Webhook-URL. Beim Scannen wird automatisch ein Lead erstellt.' },
  { key: 'telefon',   text: 'In Vapi oder Bland AI unter Webhook-Einstellungen die oben angezeigte URL als Post-Call Webhook eintragen.' },
];

export default function WebhookDashboard() {
  const { token } = useAuth();
  const fetchedRef = useRef(false);
  const [log, setLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openGuide, setOpenGuide] = useState(null);

  const mkH = () => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  });

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    fetch(`${API_BASE_URL}/api/webhooks/log`, { headers: mkH() })
      .then(r => r.json())
      .then(d => setLog(Array.isArray(d) ? d : []))
      .catch(() => toast.error('Webhook-Log konnte nicht geladen werden'))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const copyUrl = (key) => {
    const url = `${API_BASE_URL}/api/webhooks/${key}`;
    navigator.clipboard.writeText(url).then(() => toast.success('URL kopiert'));
  };

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-';

  const sourceColor = (s) => SOURCES.find(x => x.key === s)?.color || 'var(--text-tertiary)';
  const sourceLabel = (s) => SOURCES.find(x => x.key === s)?.label || s;

  const card = { background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' };
  const btnPrimary = { background: 'var(--brand-primary)', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Webhooks</h1>

      {/* ── Quellen-Karten ──────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {SOURCES.map(s => (
          <div key={s.key} style={{ ...card, padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 36, height: 36, borderRadius: 8, background: s.color, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                {s.icon}
              </div>
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{s.label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <code style={{ flex: 1, fontSize: 10, background: 'var(--bg-app)', padding: '6px 8px', borderRadius: 4, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>
                {API_BASE_URL}/api/webhooks/{s.key}
              </code>
              <button onClick={() => copyUrl(s.key)} style={btnPrimary} title="URL kopieren">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M5 11H3.5A1.5 1.5 0 012 9.5v-7A1.5 1.5 0 013.5 1h7A1.5 1.5 0 0112 2.5V5"/>
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ── Letzte Eingaenge ────────────────────────────────────── */}
      <div>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>Letzte Eingaenge</h2>
        <div style={card}>
          <div style={{
            display: 'grid', gridTemplateColumns: '120px 1fr 1fr 140px',
            gap: 12, padding: '10px 20px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)',
            borderRadius: '8px 8px 0 0',
          }}>
            {['Quelle', 'Firma', 'E-Mail', 'Datum'].map(h => (
              <span key={h} style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>{h}</span>
            ))}
          </div>

          {loading && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Laden...</div>
          )}

          {!loading && log.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Noch keine Webhook-Eingaenge.</div>
          )}

          {log.map((entry, idx) => (
            <div
              key={entry.id || idx}
              style={{
                display: 'grid', gridTemplateColumns: '120px 1fr 1fr 140px',
                gap: 12, padding: '10px 20px', alignItems: 'center',
                borderBottom: idx < log.length - 1 ? '1px solid var(--border-light)' : 'none',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div>
                <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 999, fontSize: 11, fontWeight: 500, background: sourceColor(entry.source) + '18', color: sourceColor(entry.source) }}>
                  {sourceLabel(entry.source)}
                </span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.company || '-'}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.email || '-'}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{fmtDate(entry.created_at)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Einrichtungsanleitung ───────────────────────────────── */}
      <div>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>Einrichtung</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {GUIDES.map(g => {
            const s = SOURCES.find(x => x.key === g.key);
            const isOpen = openGuide === g.key;
            return (
              <div key={g.key} style={card}>
                <button
                  onClick={() => setOpenGuide(isOpen ? null : g.key)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '12px 16px', background: 'none', border: 'none', cursor: 'pointer',
                    fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 24, height: 24, borderRadius: 6, background: s?.color || '#888', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, flexShrink: 0 }}>
                      {s?.icon}
                    </div>
                    {s?.label}
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', transition: 'transform 0.2s', transform: isOpen ? 'rotate(90deg)' : 'none' }}>&#9654;</span>
                </button>
                {isOpen && (
                  <div style={{ padding: '0 16px 14px', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {g.text}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
