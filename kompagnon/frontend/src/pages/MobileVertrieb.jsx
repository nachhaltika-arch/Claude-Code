import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';

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

  if (!isMobile) { navigate('/app/deals', { replace: true }); return null; }

  return (
    <div style={{ padding: '14px 14px 20px', background: 'var(--surface, #F0F4F5)', minHeight: '100%' }}>
      <div style={{
        fontSize: 9, fontWeight: 900, color: '#9AACAE',
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
              background: k.primary ? '#004F59' : '#fff',
              border: k.primary ? 'none' : '0.5px solid #D5E0E2',
              borderRadius: 12, padding: '16px 14px',
              cursor: 'pointer', display: 'flex', flexDirection: 'column',
              alignItems: 'flex-start', gap: 6, minHeight: 90,
              textAlign: 'left', fontFamily: 'var(--font-sans)',
              transition: 'transform .1s',
            }}
          >
            <span style={{ fontSize: 22 }}>{k.icon}</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: k.primary ? '#fff' : '#000', lineHeight: 1.3 }}>
              {k.label}
            </span>
            <span style={{ fontSize: 10, color: k.primary ? 'rgba(255,255,255,.55)' : '#9AACAE', lineHeight: 1.4 }}>
              {k.desc}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
