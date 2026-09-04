/**
 * Die drei Feldbausteine der Komponentenbibliothek (L-25).
 *
 * `Field`, `Hint` und `inputStyle` — am 2026-08-30 aus `ComponentLibrary.jsx`
 * herausgeloest. **Sie gingen zuerst**, weil beide anderen Teile sie brauchen:
 * Der KI-Erzeuger benutzt sie zwanzig Mal, der Editor einunddreissig. Blieben
 * sie bei einem, muesste der andere seinen Nachbarn importieren.
 */
import Feld from '../ui/Feld';

export function Field({ label, children }) {
  return (
    <Feld label={label} style={{ marginBottom: 12 }} labelStyle={{ color: '#475569' }}>
      {children}
    </Feld>
  );
}

export function Hint({ children }) {
  return (
    <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 3 }}>{children}</div>
  );
}

export function inputStyle(disabled) {
  return {
    width: '100%', boxSizing: 'border-box',
    padding: '7px 10px',
    border: '1px solid #cbd5e1', borderRadius: 6,
    fontSize: 12, fontFamily: 'inherit',
    background: disabled ? '#f1f5f9' : '#fff',
    color: disabled ? '#64748b' : 'inherit',
    outline: 'none',
  };
}
