import React from 'react';
import { useNavigate } from 'react-router-dom';

export function HubGrid({ children }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 10,
      padding: '0 12px 12px',
    }}>
      {children}
    </div>
  );
}

export function HubButton({ icon, label, desc, path, primary, badge, badgeStyle, onClick }) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => onClick ? onClick() : path && navigate(path)}
      style={{
        background: primary ? 'var(--brand-primary)' : 'var(--bg-surface)',
        border: primary ? 'none' : '0.5px solid var(--border-light)',
        borderRadius: 16,
        padding: '18px 14px 16px',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: 8,
        minHeight: 110,
        position: 'relative',
        overflow: 'hidden',
        fontFamily: 'var(--font-sans)',
        width: '100%',
        textAlign: 'left',
        WebkitTapHighlightColor: 'transparent',
        transition: 'transform .1s',
      }}
      onTouchStart={e => { e.currentTarget.style.transform = 'scale(0.97)'; }}
      onTouchEnd={e => { e.currentTarget.style.transform = 'scale(1)'; }}
    >
      <span style={{ fontSize: 26 }}>{icon}</span>
      <div>
        <div style={{
          fontSize: 15, fontWeight: 700,
          textTransform: 'uppercase', letterSpacing: '.03em',
          color: primary ? 'var(--text-on-brand)' : 'var(--text-primary)',
          lineHeight: 1.2,
          fontFamily: 'var(--font-sans)',
        }}>
          {label}
        </div>
        {desc && (
          <div style={{
            fontSize: 10, marginTop: 3, lineHeight: 1.4,
            // Vorher #9AACAE bzw. Weiss mit 55 % Deckkraft — beides unter der
            // Lesbarkeitsschwelle. --text-30 ist ausdruecklich kein Textton
            // (2.13 auf der App-Flaeche), und genau der stand hier.
            color: primary ? 'var(--text-on-brand)' : 'var(--text-secondary)',
            opacity: primary ? 0.85 : 1,
          }}>
            {desc}
          </div>
        )}
      </div>
      {badge && (
        <span style={{
          position: 'absolute', top: 12, right: 12,
          background: badgeStyle === 'teal' ? 'var(--status-info-bg)' : 'var(--kc-yellow)',
          color: badgeStyle === 'teal' ? 'var(--brand-primary)' : 'var(--kc-black)',
          fontSize: 8, fontWeight: 900,
          padding: '2px 7px', borderRadius: 3,
          textTransform: 'uppercase', letterSpacing: '.06em',
        }}>
          {badge}
        </span>
      )}
    </button>
  );
}

export function HubSectionLabel({ children }) {
  return (
    <div style={{
      fontSize: 9, fontWeight: 900,
      color: 'var(--text-secondary)',
      textTransform: 'uppercase',
      letterSpacing: '.1em',
      padding: '14px 14px 8px',
    }}>
      {children}
    </div>
  );
}
