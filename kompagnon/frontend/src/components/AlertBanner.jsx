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
          gap: '8px',
          marginBottom: '12px',
        }}
      >
        <ExclamationTriangleIcon style={{ width: '20px', height: '20px' }} />
        <strong style={{ fontFamily: 'var(--font-sans)', fontSize: '13px' }}>
          {alerts.length} aktive Warnung{alerts.length > 1 ? 'en' : ''}
        </strong>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {alerts.slice(0, 5).map((alert, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-surface)',
              padding: '8px 12px',
              borderRadius: 'var(--radius-md)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
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
