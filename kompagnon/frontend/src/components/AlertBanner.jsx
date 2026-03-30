import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function AlertBanner({ alerts = [] }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="kc-alert kc-alert--danger">
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--kc-space-2)',
          marginBottom: 'var(--kc-space-3)',
        }}
      >
        <ExclamationTriangleIcon style={{ width: '20px', height: '20px' }} />
        <strong style={{ fontFamily: 'var(--kc-font-display)', fontSize: 'var(--kc-text-sm)' }}>
          {alerts.length} aktive Warnung{alerts.length > 1 ? 'en' : ''}
        </strong>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-2)' }}>
        {alerts.slice(0, 5).map((alert, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--kc-weiss)',
              padding: 'var(--kc-space-2) var(--kc-space-3)',
              borderRadius: 'var(--kc-radius-md)',
              fontSize: 'var(--kc-text-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--kc-space-2)',
            }}
          >
            <span
              className="kc-badge kc-badge--danger"
              style={{ fontSize: '0.65rem', flexShrink: 0 }}
            >
              #{alert.project_id}
            </span>
            <span>{alert.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
