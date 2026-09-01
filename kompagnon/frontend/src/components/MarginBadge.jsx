/**
 * Die Marge eines Projekts als Abzeichen.
 *
 * **„unbekannt" war der Normalfall (26.08.2026) — und ist es nicht mehr.**
 * Beim Anschließen dieser Komponente (L-95) zeigte sich: `actual_hours` war
 * an **jedem** Projekt 0, `time_tracking` leer, und keine Oberfläche rief
 * `POST /api/projects/{id}/time` (L-105). Die Marge rechnete damit den
 * Festpreis minus Werkzeugkosten und kam überall auf ~97,5 %.
 *
 * **Nachgetragen am 01.09.2026:** Der zweite Halbsatz stimmt seit dem
 * 26.08. nicht mehr — `components/betrieb/Zeiterfassung.jsx` ruft `/time` am
 * Betriebsblatt, und am 31.08. kam mit `AboZeiten.jsx` die zweite Achse dazu.
 * Ein Satz, der einen behobenen Mangel weiter behauptet, schickt den
 * nächsten Leser auf die Suche nach einem Knopf, den es gibt.
 *
 * Ein grünes Abzeichen darüber ist schlimmer als keines: Es behauptet einen
 * Deckungsbeitrag, den niemand geprüft hat. Solange keine Zeit erfasst ist,
 * steht hier deshalb keine Zahl — und am Anfang eines Projekts ist das auch
 * schlicht richtig.
 *
 * Der Status kommt vom Server (`MarginCalculator.status_fuer`); die
 * Schwellen stehen dort und nicht hier.
 */
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
      background: 'var(--brand-primary-light)',
      color: 'var(--status-danger-text)',
      icon: '✗',
    },
  };

  // Ohne erfasste Zeit gibt es nichts zu zeigen — auch keinen Platzhalter
  // in Ampelfarbe. Der Hinweis nennt den Grund, damit niemand nach der Zahl
  // sucht, die hier fehlen *soll*.
  if (status === 'unbekannt') {
    return (
      <span
        className="kc-badge"
        title="Für dieses Projekt ist noch keine Arbeitszeit erfasst — eine Marge lässt sich daraus nicht ablesen."
        style={{
          background: 'var(--bg-app, transparent)',
          color: 'var(--text-tertiary)',
          border: '1px dashed var(--border-light)',
          fontFamily: 'var(--font-sans)',
          fontSize: 12, fontWeight: 600,
          padding: '3px 10px', borderRadius: 'var(--kc-radius-sm)',
        }}
      >
        Marge: keine Zeiten
      </span>
    );
  }

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
            fontSize: 12,
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
