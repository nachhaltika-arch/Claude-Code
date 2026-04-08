import wz2025 from '../data/wz2025.json';
import { useState, useRef, useEffect } from 'react';

export default function WZSearch({ value, onChange, placeholder }) {
  const [query, setQuery] = useState(value || '');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const search = (q) => {
    setQuery(q);
    if (q.length < 2) { setResults([]); setOpen(false); return; }
    const lower = q.toLowerCase();
    const found = wz2025
      .filter(item =>
        item.title?.toLowerCase().includes(lower) ||
        item.code?.toLowerCase().includes(lower)
      )
      .slice(0, 12);
    setResults(found);
    setOpen(found.length > 0);
  };

  const select = (item) => {
    const label = item.title;
    setQuery(label);
    setOpen(false);
    setResults([]);
    onChange(label);
  };

  return (
    <div ref={ref} style={{ position: 'relative', width: '100%' }}>
      <input
        type="text"
        value={query}
        onChange={e => search(e.target.value)}
        onFocus={() => query.length >= 2 && results.length > 0 && setOpen(true)}
        placeholder={placeholder || 'Gewerk suchen, z.B. Sanitaer...'}
        style={{
          width: '100%', padding: '8px 12px', fontSize: 13,
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          boxSizing: 'border-box', outline: 'none',
          fontFamily: 'var(--font-sans)',
        }}
      />
      {open && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0,
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          zIndex: 9999, maxHeight: 280, overflowY: 'auto',
          marginTop: 4,
        }}>
          {results.map((item, i) => (
            <div key={i} onClick={() => select(item)}
              style={{
                padding: '8px 12px', cursor: 'pointer',
                borderBottom: '1px solid var(--border-light)',
                display: 'flex', gap: 10, alignItems: 'flex-start',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-active)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{
                fontSize: 10, fontWeight: 700, color: 'var(--brand-primary)',
                background: 'var(--bg-active)', borderRadius: 4,
                padding: '2px 6px', flexShrink: 0, marginTop: 1,
                fontFamily: 'var(--font-mono)',
              }}>
                {item.code}
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                {item.title}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
