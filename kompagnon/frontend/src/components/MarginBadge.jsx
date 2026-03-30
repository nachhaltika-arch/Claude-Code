import React from 'react';

export default function MarginBadge({ marginPercent, status = 'green' }) {
  const styles = {
    green: {
      background: '#e8f5e9',
      color: 'var(--kc-success)',
      icon: '✓',
    },
    yellow: {
      background: '#fff3e0',
      color: 'var(--kc-warning)',
      icon: '⚠',
    },
    red: {
      background: 'var(--kc-rot-subtle)',
      color: 'var(--kc-rot)',
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
        fontFamily: 'var(--kc-font-mono)',
        fontSize: 'var(--kc-text-sm)',
        fontWeight: 700,
        padding: 'var(--kc-space-1) var(--kc-space-3)',
        borderRadius: 'var(--kc-radius-sm)',
      }}
    >
      {marginPercent?.toFixed(1)}% {s.icon}
      {status === 'red' && (
        <span
          style={{
            marginLeft: 'var(--kc-space-2)',
            fontSize: 'var(--kc-text-xs)',
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
