import { useState, useEffect, useRef } from 'react';
import wzData from '../data/wz2025.json';

export default function WZSearch({ value, onChange, placeholder = 'Branche suchen...' }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const results = query.length >= 2
    ? (() => {
        const q = query.toLowerCase();
        const matches = wzData.filter(
          e => e.title.toLowerCase().includes(q) || e.code.startsWith(query)
        );
        const primary = matches.filter(e => e.level <= 3);
        const secondary = matches.filter(e => e.level > 3);
        return [...primary, ...secondary].slice(0, 30);
      })()
    : [];

  const handleSelect = (entry) => {
    onChange(entry);
    setQuery('');
    setOpen(false);
  };

  const handleClear = (e) => {
    e.stopPropagation();
    onChange(null);
    setQuery('');
  };

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      {/* Input */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 10px',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-md)',
        background: 'var(--bg-app)',
        cursor: 'text',
      }} onClick={() => !value && setOpen(true)}>
        <span style={{ fontSize: 14, flexShrink: 0, color: 'var(--text-tertiary)' }}>🔍</span>
        {value ? (
          <>
            <span style={{ flex: 1, fontSize: 13, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <span style={{ fontFamily: 'monospace', color: 'var(--text-tertiary)', marginRight: 6 }}>{value.code}</span>
              {value.title}
            </span>
            <button onClick={handleClear} style={{
              flexShrink: 0, background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-tertiary)', fontSize: 14, padding: 0, lineHeight: 1,
              fontFamily: 'var(--font-sans)',
            }}>✕</button>
          </>
        ) : (
          <input
            value={query}
            onChange={e => { setQuery(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            placeholder={placeholder}
            style={{
              flex: 1, border: 'none', outline: 'none', background: 'transparent',
              fontSize: 13, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)',
            }}
          />
        )}
      </div>

      {/* Dropdown */}
      {open && !value && query.length >= 2 && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 4px)', left: 0, right: 0,
          background: 'var(--bg-surface)', border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-md)', boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          zIndex: 100, maxHeight: 320, overflowY: 'auto',
        }}>
          {results.length === 0 ? (
            <div style={{ padding: '12px 14px', fontSize: 13, color: 'var(--text-tertiary)' }}>
              Keine Ergebnisse für „{query}"
            </div>
          ) : results.map((entry, i) => (
            <div
              key={i}
              onClick={() => handleSelect(entry)}
              style={{
                display: 'flex', alignItems: 'baseline', gap: 10,
                padding: `7px 14px 7px ${14 + (entry.level - 1) * 8}px`,
                cursor: 'pointer', borderBottom: '1px solid var(--border-light)',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-active)'}
              onMouseLeave={e => e.currentTarget.style.background = ''}
            >
              <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-tertiary)', flexShrink: 0, minWidth: 52 }}>
                {entry.code}
              </span>
              <span style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {entry.title}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
