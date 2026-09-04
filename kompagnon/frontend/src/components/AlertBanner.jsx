/**
 * Die aktiven Warnungen des Innendienstes.
 *
 * **Angeschlossen am 26.08.2026 (L-95).** Der Scheduler berechnet taeglich
 * ueberfaellige Phasen, kritische Margen und Scope-Creep; `GET
 * /api/dashboard/alerts` gibt sie heraus, und dieses Bauteil zeigt sie an.
 * Nur importiert hat es niemand — gebaut, nie verdrahtet, dieselbe Familie
 * wie `PageHeader` (L-17, am 26.08.2026 entfernt) und die vier
 * unerreichbaren Reiter (L-128).
 *
 * `onOeffnen` ist neu und der Grund, warum die Zeilen Schaltflaechen sind:
 * Eine Warnung, die „Projekt 12" nennt und keinen Weg dorthin hat, verlangt
 * vom Leser, die Nummer zu merken und selbst zu suchen. Fehlt die Zusage,
 * bleiben es Textzeilen — dann ist auch keine Schaltflaeche da, die ins
 * Leere fuehrt.
 */
import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function AlertBanner({ alerts = [], onOeffnen }) {
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
        {alerts.slice(0, 5).map((alert, idx) => {
          const zeile = (
            <>
              <span
                className="kc-badge kc-badge--danger"
                style={{ flexShrink: 0 }}
              >
                #{alert.project_id}
              </span>
              <span>{alert.message}</span>
            </>
          );
          const stil = {
            background: 'var(--bg-surface)',
            padding: '8px 12px',
            borderRadius: 'var(--radius-md)',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            textAlign: 'left',
            width: '100%',
          };

          // Eine echte `<button>` statt `role="button"` — sie ist von sich
          // aus in der Tabulatorreihenfolge und reagiert auf Enter und
          // Leertaste, ohne dass es jemand nachbauen muss (L-17).
          return onOeffnen ? (
            <button key={idx} type="button"
              onClick={() => onOeffnen(alert)}
              style={{ ...stil, border: 'none', cursor: 'pointer',
                       font: 'inherit', color: 'inherit' }}>
              {zeile}
            </button>
          ) : (
            <div key={idx} style={stil}>{zeile}</div>
          );
        })}
      </div>
    </div>
  );
}
