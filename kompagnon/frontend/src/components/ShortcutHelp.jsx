import { createPortal } from 'react-dom';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';

const SHORTCUTS = [
  { keys: ['⌘', 'K'], desc: 'Command Palette öffnen' },
  { keys: ['⌘', ','], desc: 'Einstellungen öffnen' },
  { keys: ['⌘', 'H'], desc: 'Dashboard öffnen' },
  { keys: ['Esc'],     desc: 'Modal / Palette schließen' },
  { keys: ['?'],       desc: 'Diese Übersicht' },
  { keys: ['Tab'],     desc: 'Nächstes Feld im Formular' },
];

export default function ShortcutHelp({ open, onClose }) {
  useEscapeKey(onClose, open);
  if (!open) return null;

  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 8500,
        background: 'rgba(15,28,32,0.5)',
        backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-xl, 16px)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-xl)',
          padding: '24px 28px', maxWidth: 380, width: '100%',
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 18 }}>
          Keyboard Shortcuts
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {SHORTCUTS.map((s, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{s.desc}</span>
              <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
                {s.keys.map((k, j) => (
                  <kbd key={j} style={{
                    fontSize: 11, padding: '2px 7px', borderRadius: 5,
                    background: 'var(--bg-app)',
                    border: '1px solid var(--border-medium)',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                    boxShadow: '0 1px 0 var(--border-medium)',
                  }}>{k}</kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 20, fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'center' }}>
          <kbd style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>Esc</kbd> oder klicke außerhalb zum Schließen
        </div>
      </div>
    </div>,
    document.body
  );
}
