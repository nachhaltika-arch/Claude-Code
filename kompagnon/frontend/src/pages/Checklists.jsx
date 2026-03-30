import React from 'react';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';

export default function Checklists() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      <div className="kc-section-header">
        <span className="kc-eyebrow">Qualitätssicherung</span>
        <h1>Checklisten</h1>
      </div>
      <div
        className="kc-card"
        style={{
          textAlign: 'center',
          padding: 'var(--kc-space-16)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--kc-space-4)',
        }}
      >
        <ClipboardDocumentListIcon
          style={{ width: '48px', height: '48px', color: 'var(--kc-anthrazit-20)' }}
        />
        <div>
          <p style={{ fontWeight: 700, color: 'var(--kc-text-primaer)', fontSize: 'var(--kc-text-lg)' }}>
            Checklisten-Management
          </p>
          <p style={{ color: 'var(--kc-mittel)', fontSize: 'var(--kc-text-sm)' }}>
            54 Items across 7 Phasen — In Entwicklung
          </p>
        </div>
      </div>
    </div>
  );
}
