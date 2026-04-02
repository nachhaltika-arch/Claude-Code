import React from 'react';

export default function MarginBadge({ marginPercent, status = 'green' }) {
  const styles = {
    green: {
      background: '#e8f5e9',
      color: 'var(--status-success-text)',
      icon: '✓',
    },
    yellow: {
      background: 'var(--status-warning-bg)',
      color: 'var(--status-warning-text)',
      icon: '⚠',
    },
    red: {
      background: 'var(--kc-rot-subtle)',
      color: 'var(--brand-primary)',
      icon: '✗',
    },
  };

  const s = styles[status] || styles.green;

  return (
    <span
      className="kc-badge"
      style={{
        background: s.background,
        color: s.color,
        fontFamily: 'var(--font-mono)',
        fontSize: '13px',
        fontWeight: 700,
        padding: '4px 12px',
        borderRadius: 'var(--kc-radius-sm)',
      }}
    >
      {marginPercent?.toFixed(1)}% {s.icon}
      {status === 'red' && (
        <span
          style={{
            marginLeft: '8px',
            fontSize: '11px',
            textTransform: 'uppercase',
            letterSpacing: 'var(--kc-tracking-wide)',
          }}
        >
          ESKALIEREN
        </span>
      )}
    </span>
  );
}
