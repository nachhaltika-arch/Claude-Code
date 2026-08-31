import React from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import SeitenTitel from '../components/ui/SeitenTitel';

const KACHELN = [
  { label: 'Pipeline',      desc: 'Deals & Phasen',      icon: '📋', path: '/app/deals',      primary: true },
  { label: 'Audit-Tool',    desc: 'Website analysieren',  icon: '🔍', path: '/app/audit' },
  { label: 'Kampagnen',     desc: 'UTM & Landingpages',   icon: '📣', path: '/app/campaigns' },
  { label: 'Newsletter',    desc: 'Brevo · Listen',       icon: '📧', path: '/app/newsletter' },
  { label: 'Domain-Import', desc: 'CSV hochladen',        icon: '⬆️', path: '/app/import' },
  { label: 'Retainer',      desc: 'Pflegepakete',         icon: '💰', path: '/app/retainer' },
];

export default function MobileVertrieb() {
  const navigate = useNavigate();
  const { isMobile } = useScreenSize();

  // `navigate()` im Rumpf leitet nicht um — der Router verwirft den Aufruf.
  // Diese Adresse steht in der Mobilleiste; auf einem breiten Bildschirm
  // zeigte sie deshalb eine leere Seite (nachgemessen am 18.08.2026).
  if (!isMobile) return <Navigate to="/app/deals" replace />;

  return (
    <div style={{ padding: '14px 14px 20px', background: 'var(--bg-app)', minHeight: '100%' }}>
      <SeitenTitel>Vertrieb unterwegs</SeitenTitel>
      <div style={{
        fontSize: 9, fontWeight: 900, color: 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 12,
      }}>
        Was möchtest du tun?
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {KACHELN.map(k => (
          <button
            key={k.path}
            onClick={() => navigate(k.path)}
            onTouchStart={e => { e.currentTarget.style.transform = 'scale(0.97)'; }}
            onTouchEnd={e => { e.currentTarget.style.transform = 'scale(1)'; }}
            style={{
              background: k.primary ? 'var(--brand-primary)' : 'var(--bg-surface)',
              border: k.primary ? 'none' : '0.5px solid var(--border-light)',
              borderRadius: 12, padding: '16px 14px',
              cursor: 'pointer', display: 'flex', flexDirection: 'column',
              alignItems: 'flex-start', gap: 6, minHeight: 90,
              textAlign: 'left', fontFamily: 'var(--font-sans)',
              transition: 'transform .1s',
            }}
          >
            <span style={{ fontSize: 22 }}>{k.icon}</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: k.primary ? 'var(--text-on-brand)' : 'var(--text-primary)', lineHeight: 1.3 }}>
              {k.label}
            </span>
            <span style={{ fontSize: 12, color: k.primary ? 'var(--text-on-brand)' : 'var(--text-secondary)', opacity: k.primary ? 0.85 : 1, lineHeight: 1.4 }}>
              {k.desc}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
