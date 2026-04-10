import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';

const COMMANDS = [
  { id: 'dashboard',   label: 'Dashboard',          icon: '🏠', path: '/app/dashboard',      keywords: ['home', 'start', 'übersicht'] },
  { id: 'projects',    label: 'Kundenprojekte',      icon: '📋', path: '/app/projects',       keywords: ['projekte', 'kunden'] },
  { id: 'deals',       label: 'Deals',               icon: '📊', path: '/app/deals',          keywords: ['leads', 'vertrieb', 'pipeline'] },
  { id: 'companies',   label: 'Unternehmen',         icon: '🏢', path: '/app/companies',      keywords: ['firmen', 'unternehmen'] },
  { id: 'audit',       label: 'Website Audit',       icon: '🔍', path: '/app/audit',          keywords: ['audit', 'website', 'check'] },
  { id: 'newsletter',  label: 'Newsletter',          icon: '📧', path: '/app/newsletter',     keywords: ['mail', 'kampagne'] },
  { id: 'tickets',     label: 'Support Tickets',     icon: '🎫', path: '/app/tickets',        keywords: ['support', 'hilfe'] },
  { id: 'academy',     label: 'Akademie',            icon: '🎓', path: '/app/academy',        keywords: ['lernen', 'kurse', 'akademie'] },
  { id: 'import',      label: 'Domain Import',       icon: '⬆️', path: '/app/import',         keywords: ['import', 'csv', 'domain'] },
  { id: 'settings',    label: 'Einstellungen',       icon: '⚙️', path: '/app/settings',       keywords: ['settings', 'profil', 'konto'] },
  { id: 'users',       label: 'Benutzerverwaltung',  icon: '👥', path: '/app/settings/users', keywords: ['user', 'nutzer'] },
  { id: 'pages',       label: 'Seiten-Manager',      icon: '🌐', path: '/app/pages',          keywords: ['seiten', 'pages', 'landing'] },
  { id: 'retainer',    label: 'Retainer',            icon: '💰', path: '/app/retainer',       keywords: ['retainer', 'abo'] },
];

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const inputRef = useRef(null);

  useEscapeKey(onClose, open);

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  const filtered = COMMANDS.filter(c => {
    if (!query) return true;
    const q = query.toLowerCase();
    return c.label.toLowerCase().includes(q)
      || c.keywords.some(k => k.includes(q));
  });

  const go = (path) => { navigate(path); onClose(); };

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelected(s => Math.min(s + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelected(s => Math.max(s - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selected]) go(filtered[selected].path);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, filtered, selected]);

  if (!open) return null;

  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 9000,
        background: 'rgba(15,28,32,0.6)',
        backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        padding: '80px 20px 20px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-xl, 16px)',
          boxShadow: 'var(--shadow-xl)',
          width: '100%', maxWidth: 520,
          overflow: 'hidden',
        }}
      >
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '14px 18px',
          borderBottom: '1px solid var(--border-light)',
        }}>
          <span style={{ fontSize: 16, color: 'var(--text-tertiary)', flexShrink: 0 }}>🔍</span>
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setSelected(0); }}
            placeholder="Wohin möchtest du navigieren?"
            style={{
              flex: 1, border: 'none', outline: 'none',
              fontSize: 15, background: 'transparent',
              color: 'var(--text-primary)', fontFamily: 'var(--font-sans)',
            }}
          />
          <kbd style={{
            fontSize: 10, padding: '2px 6px', borderRadius: 4,
            background: 'var(--bg-app)', border: '1px solid var(--border-light)',
            color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)',
            flexShrink: 0,
          }}>Esc</kbd>
        </div>

        <div style={{ maxHeight: 360, overflowY: 'auto', padding: '6px 0' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px 18px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
              Keine Ergebnisse für „{query}"
            </div>
          ) : (
            filtered.map((cmd, i) => (
              <button
                key={cmd.id}
                onClick={() => go(cmd.path)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                  padding: '10px 18px', border: 'none', textAlign: 'left',
                  background: i === selected ? 'var(--bg-active)' : 'transparent',
                  cursor: 'pointer', fontFamily: 'var(--font-sans)',
                  transition: 'background var(--transition-fast)',
                }}
                onMouseEnter={() => setSelected(i)}
              >
                <span style={{
                  width: 32, height: 32, borderRadius: 'var(--radius-sm)',
                  background: i === selected ? 'var(--brand-primary)' : 'var(--bg-app)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 15, flexShrink: 0,
                  transition: 'background var(--transition-fast)',
                }}>
                  {cmd.icon}
                </span>
                <span style={{
                  fontSize: 14, fontWeight: i === selected ? 600 : 400,
                  color: i === selected ? 'var(--brand-primary-dark)' : 'var(--text-primary)',
                }}>
                  {cmd.label}
                </span>
                {i === selected && (
                  <kbd style={{
                    marginLeft: 'auto', fontSize: 10, padding: '2px 6px',
                    borderRadius: 4, background: 'var(--brand-primary-light)',
                    color: 'var(--brand-primary-dark)',
                    fontFamily: 'var(--font-mono)', flexShrink: 0,
                  }}>↵</kbd>
                )}
              </button>
            ))
          )}
        </div>

        <div style={{
          borderTop: '1px solid var(--border-light)',
          padding: '8px 18px',
          display: 'flex', gap: 16,
          fontSize: 11, color: 'var(--text-tertiary)',
        }}>
          <span><kbd style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>↑↓</kbd> navigieren</span>
          <span><kbd style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>↵</kbd> öffnen</span>
          <span><kbd style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>Esc</kbd> schließen</span>
        </div>
      </div>
    </div>,
    document.body
  );
}
