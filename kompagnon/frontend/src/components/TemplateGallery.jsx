import { useEffect, useState } from 'react';
import API_BASE_URL from '../config';
import { allTemplates as localTemplates } from '../data/allTemplates';

export default function TemplateGallery({ onSelect, onClose }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('Alle');

  useEffect(() => {
    const token = sessionStorage.getItem('kompagnon_token');
    fetch(`${API_BASE_URL}/api/templates/`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(data => {
        const fetched = Array.isArray(data) ? data : (data.results || []);
        setTemplates(fetched.length > 0 ? fetched : localTemplates);
      })
      .catch(() => setTemplates(localTemplates))
      .finally(() => setLoading(false));
  }, []);

  const categories = [
    'Alle',
    ...Array.from(new Set(templates.map(t => t.category).filter(Boolean))),
  ];

  const visible =
    activeCategory === 'Alle'
      ? templates
      : templates.filter(t => t.category === activeCategory);

  /* ── styles ── */
  const overlayStyle = {
    position: 'fixed',
    inset: 0,
    zIndex: 9998,
    background: 'rgba(0,0,0,0.75)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const modalStyle = {
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
    maxWidth: 1100,
    width: '100%',
    margin: '0 auto',
    background: '#f4f6f9',
    borderRadius: 0,
    overflow: 'hidden',
  };

  const headerStyle = {
    background: '#1a2332',
    color: '#fff',
    padding: '1rem 1.5rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexShrink: 0,
  };

  const closeBtnStyle = {
    background: 'transparent',
    border: '1px solid rgba(255,255,255,0.35)',
    color: '#fff',
    borderRadius: 6,
    padding: '0.3rem 0.75rem',
    cursor: 'pointer',
    fontSize: 18,
    lineHeight: 1,
  };

  const filterBarStyle = {
    background: '#fff',
    borderBottom: '1px solid #dee2e6',
    padding: '0.75rem 1.5rem',
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
    flexShrink: 0,
  };

  const categoryBtnBase = {
    padding: '0.35rem 0.9rem',
    borderRadius: 20,
    border: '1px solid #dee2e6',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    transition: 'all 0.15s',
  };

  const gridWrapStyle = {
    flex: 1,
    overflowY: 'auto',
    padding: '1.5rem',
  };

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1.25rem',
  };

  const cardStyle = {
    background: '#fff',
    borderRadius: 10,
    boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  };

  const thumbnailStyle = {
    height: 140,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 52,
    background: 'linear-gradient(135deg,#e9ecef,#dee2e6)',
    flexShrink: 0,
  };

  const cardBodyStyle = {
    padding: '0.9rem 1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    flex: 1,
  };

  const badgeStyle = {
    display: 'inline-block',
    background: '#e7f1ff',
    color: '#0d6efd',
    borderRadius: 12,
    padding: '0.2rem 0.6rem',
    fontSize: 11,
    fontWeight: 600,
    alignSelf: 'flex-start',
  };

  const selectBtnStyle = {
    marginTop: 'auto',
    background: '#0d6efd',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    padding: '0.55rem 1rem',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
  };

  const centeredStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    padding: '3rem',
    color: '#6c757d',
    fontSize: 16,
  };

  /* ── thumbnail color helpers ── */
  const thumbColors = [
    '#cfe2ff', '#d1e7dd', '#fff3cd', '#f8d7da',
    '#e2d9f3', '#d3e9f7', '#fde8d0', '#d5f5e3',
  ];

  function thumbBg(idx) {
    return thumbColors[idx % thumbColors.length];
  }

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <div>
            <span style={{ fontSize: 20, fontWeight: 700 }}>Vorlagen-Galerie</span>
            {!loading && (
              <span
                style={{
                  marginLeft: '0.75rem',
                  fontSize: 13,
                  opacity: 0.65,
                  fontWeight: 400,
                }}
              >
                {templates.length} Vorlage{templates.length !== 1 ? 'n' : ''}
              </span>
            )}
          </div>
          <button style={closeBtnStyle} onClick={onClose} title="Schließen">
            ✕
          </button>
        </div>

        {/* Category filter bar */}
        {!loading && templates.length > 0 && (
          <div style={filterBarStyle}>
            {categories.map(cat => (
              <button
                key={cat}
                style={{
                  ...categoryBtnBase,
                  background: activeCategory === cat ? '#0d6efd' : '#fff',
                  color: activeCategory === cat ? '#fff' : '#495057',
                  borderColor: activeCategory === cat ? '#0d6efd' : '#dee2e6',
                }}
                onClick={() => setActiveCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div style={centeredStyle}>
            <div>
              <div
                style={{
                  width: 40,
                  height: 40,
                  border: '4px solid #dee2e6',
                  borderTopColor: '#0d6efd',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                  margin: '0 auto 1rem',
                }}
              />
              Vorlagen werden geladen…
              <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            </div>
          </div>
        ) : visible.length === 0 ? (
          <div style={centeredStyle}>
            {templates.length === 0
              ? 'Keine Vorlagen verfügbar.'
              : `Keine Vorlagen in der Kategorie „${activeCategory}".`}
          </div>
        ) : (
          <div style={gridWrapStyle}>
            <div style={gridStyle}>
              {visible.map((tpl, idx) => (
                <div key={tpl.id || tpl.name || idx} style={cardStyle}>
                  <div
                    style={{
                      ...thumbnailStyle,
                      background: `linear-gradient(135deg, ${thumbBg(idx)}, #fff)`,
                    }}
                  >
                    {tpl.emoji || '📄'}
                  </div>
                  <div style={cardBodyStyle}>
                    <div style={{ fontWeight: 700, fontSize: 15, color: '#1a2332' }}>
                      {tpl.name || 'Vorlage'}
                    </div>
                    {tpl.category && (
                      <span style={badgeStyle}>{tpl.category}</span>
                    )}
                    <button
                      style={selectBtnStyle}
                      onClick={() =>
                        onSelect({ html: tpl.html || '', name: tpl.name || 'Vorlage' })
                      }
                    >
                      Auswählen
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
