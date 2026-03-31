import React from 'react';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';

export default function Checklists() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div >
        <span >Qualitätssicherung</span>
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
          gap: '16px',
        }}
      >
        <ClipboardDocumentListIcon
          style={{ width: '48px', height: '48px', color: 'var(--kc-anthrazit-20)' }}
        />
        <div>
          <p style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '16px' }}>
            Checklisten-Management
          </p>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '13px' }}>
            54 Items across 7 Phasen — In Entwicklung
          </p>
        </div>
      </div>
    </div>
  );
}
