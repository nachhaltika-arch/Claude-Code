/**
 * Zwei Darstellungshelfer der Analyse-Zentrale (L-25).
 *
 * `DetailLabel` und `HeadingRow`. Am 2026-08-30 herausgeloest — der letzte
 * Schnitt, der die Zentrale unter die 800-Zeilen-Grenze bringt.
 */


export function DetailLabel({ children, style }) {
  return (
    <div style={{
      fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)',
      textTransform: 'uppercase', letterSpacing: '.08em',
      marginBottom: 8, ...style,
    }}>
      {children}
    </div>
  );
}

export function HeadingRow({ level, text, color, indent }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, paddingLeft: indent }}>
      <span style={{ fontSize: 9, fontWeight: 800, color, opacity: 0.6, flexShrink: 0, marginTop: 3, letterSpacing: '.04em', minWidth: 20 }}>
        {level}
      </span>
      <span style={{ fontSize: 13, color, lineHeight: 1.5 }}>{text}</span>
    </div>
  );
}

// ── Projekt-Zusammenfassung (linke Spalte unten) ─────────────────────────────

