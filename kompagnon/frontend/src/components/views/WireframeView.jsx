/**
 * WireframeView — Block-Canvas pro Sitemap-Seite mit Tausch- und Hinzufügen-
 * Panel. Liest Component-Library aus /api/components, persistiert Änderungen
 * via POST /api/projects/{id}/wireframe.
 *
 * Props:
 *   projectId
 *   leadId
 *   wireframeData            — { pages: [{page_id, page_name, blocks: [...]}] }
 *   onWireframeChange(next)  — wird nach jedem Save aufgerufen
 *   onNavigateToStyleGuide   — View-Switcher
 */
import { useEffect, useMemo, useState, useCallback } from 'react';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

const CATEGORIES = ['Alle', 'NAV', 'HERO', 'LEIST', 'TRUST', 'SEO', 'CTA', 'HW', 'FOOT'];

// W1 Relume-Parität: Responsive-Preview-Breiten. Werte entsprechen den
// Standard-Devices, die Relume's Wireframe-Builder anbietet.
const PREVIEW_WIDTHS = {
  mobile:  '375px',
  tablet:  '768px',
  desktop: '100%',
};

export default function WireframeView({
  projectId,
  leadId,
  wireframeData,
  onWireframeChange,
  onNavigateToStyleGuide,
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const pages = wireframeData?.pages || [];
  const [activePageId, setActivePageId] = useState(pages[0]?.page_id || null);
  const [library, setLibrary] = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [swapPanel, setSwapPanel] = useState({ open: false, targetIdx: null, mode: 'swap' }); // mode: swap|add
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('Alle');
  const [saving, setSaving] = useState(false);
  // W1 Relume-Parität: Preview-Width-Toggle ('mobile' | 'tablet' | 'desktop')
  const [previewSize, setPreviewSize] = useState('desktop');
  // W1 Drag-Reorder-State (native HTML5 DnD)
  const [draggedIdx, setDraggedIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);

  // Default-Page auf erste setzen sobald Daten reinkommen
  useEffect(() => {
    if (!activePageId && pages.length > 0) {
      setActivePageId(pages[0].page_id);
    }
  }, [pages, activePageId]);

  // Component-Library beim ersten Mount eagerly laden — die BlockCards
  // brauchen html_template für Live-Preview, sonst zeigen sie leere Karten
  // bevor der User das Swap-Panel öffnet.
  useEffect(() => {
    if (library.length > 0) return;
    setLibraryLoading(true);
    fetch(`${API_BASE_URL}/api/components`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setLibrary(Array.isArray(data) ? data : []))
      .finally(() => setLibraryLoading(false));
  }, [library.length, headers]);

  const activePage = pages.find((p) => p.page_id === activePageId) || null;
  const activeBlocks = (activePage?.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const filteredLibrary = useMemo(() => {
    let list = library;
    if (activeCategory !== 'Alle') {
      list = list.filter((c) => c.category === activeCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      list = list.filter(
        (c) =>
          c.slug.toLowerCase().includes(q) ||
          c.name.toLowerCase().includes(q) ||
          (c.tags || []).some((t) => t.toLowerCase().includes(q)),
      );
    }
    return list;
  }, [library, activeCategory, searchQuery]);

  // ── Mutationen am Wireframe ─────────────────────────────────────────────────

  const persist = useCallback(
    async (nextData) => {
      setSaving(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/wireframe`, {
          method: 'POST',
          headers,
          body: JSON.stringify(nextData),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        onWireframeChange?.(nextData);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.warn('wireframe save failed:', e);
      } finally {
        setSaving(false);
      }
    },
    [projectId, headers, onWireframeChange],
  );

  const swapBlock = (targetIdx, newSlug) => {
    if (!activePage) return;
    const lib = library.find((c) => c.slug === newSlug);
    const defaultSlots = (lib?.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    const nextBlocks = activeBlocks.map((b, i) =>
      i === targetIdx ? { slug: newSlug, order: b.order ?? i, slots: defaultSlots } : b,
    );
    const nextData = {
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
    setSwapPanel({ open: false, targetIdx: null, mode: 'swap' });
  };

  const addBlock = (newSlug) => {
    if (!activePage) return;
    const lib = library.find((c) => c.slug === newSlug);
    const defaultSlots = (lib?.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    const order = activeBlocks.length;
    const nextBlocks = [...activeBlocks, { slug: newSlug, order, slots: defaultSlots }];
    const nextData = {
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
    setSwapPanel({ open: false, targetIdx: null, mode: 'swap' });
  };

  const removeBlock = (targetIdx) => {
    if (!activePage) return;
    const nextBlocks = activeBlocks
      .filter((_, i) => i !== targetIdx)
      .map((b, i) => ({ ...b, order: i }));
    const nextData = {
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
  };

  // W1: Drag-Reorder — verschiebt Block von fromIdx an toIdx, persistiert.
  const moveBlock = (fromIdx, toIdx) => {
    if (!activePage || fromIdx === toIdx || fromIdx == null || toIdx == null) return;
    const next = [...activeBlocks];
    const [moved] = next.splice(fromIdx, 1);
    next.splice(toIdx, 0, moved);
    const nextBlocks = next.map((b, i) => ({ ...b, order: i }));
    const nextData = {
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  if (pages.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: '#64748b', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>📐</div>
        <div style={{ fontSize: 15, fontWeight: 600, color: KC_DARK, marginBottom: 6 }}>
          Noch kein Wireframe vorhanden
        </div>
        <div style={{ fontSize: 13 }}>
          Wechsle zur Sitemap-Ansicht und starte den KI-Wireframe-Generator.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: '100%', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      {/* Linke Spalte: Seiten-Liste */}
      <aside
        style={{
          width: 180,
          flexShrink: 0,
          background: '#f8fafc',
          borderRight: '1px solid #e2e8f0',
          padding: '16px 8px',
          overflowY: 'auto',
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0 8px', marginBottom: 8 }}>
          Seiten
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {pages.map((p) => (
            <li key={p.page_id}>
              <button
                type="button"
                onClick={() => setActivePageId(p.page_id)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 10px',
                  borderRadius: 6,
                  border: 'none',
                  background: p.page_id === activePageId ? KC_DARK : 'transparent',
                  color: p.page_id === activePageId ? '#fff' : '#334155',
                  fontSize: 12,
                  fontWeight: p.page_id === activePageId ? 700 : 500,
                  cursor: 'pointer',
                }}
              >
                <div>{p.page_name || `Seite ${p.page_id}`}</div>
                <div style={{ fontSize: 10, opacity: 0.7, marginTop: 2 }}>
                  {(p.blocks || []).length} Blöcke
                </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>

      {/* Mittlere Spalte: Block-Canvas der aktiven Seite */}
      <main style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
        {/* Topbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 20,
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 900, color: KC_DARK, margin: 0, textTransform: 'uppercase' }}>
              {activePage?.page_name || 'Seite'}
            </h1>
            <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
              {activeBlocks.length} Block{activeBlocks.length === 1 ? '' : 's'}
              {saving && ' · speichert…'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* W1 Relume-Parität: Responsive-Preview-Toggle */}
            <div style={{
              display: 'inline-flex', gap: 0,
              border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden',
            }}>
              {[
                { id: 'mobile',  label: '📱', title: 'Mobile (375px)' },
                { id: 'tablet',  label: '📲', title: 'Tablet (768px)' },
                { id: 'desktop', label: '🖥', title: 'Desktop (volle Breite)' },
              ].map((s) => {
                const active = previewSize === s.id;
                return (
                  <button
                    key={s.id} type="button" title={s.title}
                    onClick={() => setPreviewSize(s.id)}
                    style={{
                      background: active ? KC_DARK : 'transparent',
                      color: active ? '#fff' : '#475569',
                      border: 'none', cursor: 'pointer',
                      padding: '6px 10px', fontSize: 14, lineHeight: 1,
                      fontFamily: 'inherit',
                    }}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              onClick={() => setSwapPanel({ open: true, targetIdx: null, mode: 'add' })}
              style={{
                background: 'transparent',
                color: KC_DARK,
                border: `1.5px solid ${KC_DARK}`,
                borderRadius: 8,
                padding: '8px 14px',
                fontSize: 12,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              + Block hinzufügen
            </button>
            <button
              type="button"
              onClick={onNavigateToStyleGuide}
              disabled={activeBlocks.length === 0}
              style={{
                background: KC_MID,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                padding: '9px 16px',
                fontSize: 12,
                fontWeight: 700,
                cursor: activeBlocks.length === 0 ? 'not-allowed' : 'pointer',
                opacity: activeBlocks.length === 0 ? 0.5 : 1,
              }}
            >
              Zu Style Guide →
            </button>
          </div>
        </div>

        {/* W1: Block-Liste mit Live-Preview + native Drag-Reorder.
            Container-Width entspricht dem Preview-Size-Toggle (mobile/tablet/desktop). */}
        <div style={{
          margin: '0 auto',
          maxWidth: PREVIEW_WIDTHS[previewSize],
          width: '100%',
          transition: 'max-width 0.2s ease',
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {activeBlocks.map((b, idx) => (
              <BlockCard
                key={`${b.slug}-${idx}`}
                idx={idx}
                block={b}
                libraryEntry={library.find((c) => c.slug === b.slug)}
                isDragOver={dragOverIdx === idx && draggedIdx !== idx}
                isDragging={draggedIdx === idx}
                onDragStart={() => setDraggedIdx(idx)}
                onDragOver={(e) => { e.preventDefault(); setDragOverIdx(idx); }}
                onDrop={() => { moveBlock(draggedIdx, idx); setDraggedIdx(null); setDragOverIdx(null); }}
                onDragEnd={() => { setDraggedIdx(null); setDragOverIdx(null); }}
                onSwap={() => setSwapPanel({ open: true, targetIdx: idx, mode: 'swap' })}
                onRemove={() => removeBlock(idx)}
              />
            ))}
            {activeBlocks.length === 0 && (
              <div
                style={{
                  textAlign: 'center',
                  padding: 32,
                  border: '2px dashed #cbd5e1',
                  borderRadius: 12,
                  color: '#94a3b8',
                  fontSize: 13,
                }}
              >
                Diese Seite hat noch keine Blöcke. Klick auf „+ Block hinzufügen".
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Rechtes Slide-In-Panel: Block-Tausch / Hinzufügen */}
      {swapPanel.open && (
        <aside
          style={{
            width: 340,
            flexShrink: 0,
            background: '#fff',
            borderLeft: '1px solid #e2e8f0',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '-4px 0 12px rgba(0,0,0,0.04)',
          }}
        >
          <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK, textTransform: 'uppercase' }}>
                {swapPanel.mode === 'swap' ? 'Block tauschen' : 'Block hinzufügen'}
              </div>
              <button
                type="button"
                onClick={() => setSwapPanel({ open: false, targetIdx: null, mode: 'swap' })}
                aria-label="Schließen"
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#64748b' }}
              >
                ✕
              </button>
            </div>
            <input
              type="text"
              placeholder="Suchen…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 10px',
                border: '1px solid #cbd5e1',
                borderRadius: 6,
                fontSize: 12,
                outline: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: 4, padding: '8px 12px', borderBottom: '1px solid #e2e8f0', overflowX: 'auto' }}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                style={{
                  padding: '4px 10px',
                  border: 'none',
                  borderRadius: 4,
                  background: activeCategory === cat ? KC_DARK : 'transparent',
                  color: activeCategory === cat ? '#fff' : '#475569',
                  fontSize: 10,
                  fontWeight: 700,
                  cursor: 'pointer',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  flexShrink: 0,
                }}
              >
                {cat}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {libraryLoading && <div style={{ padding: 16, color: '#64748b', fontSize: 12 }}>Lädt…</div>}
            {!libraryLoading && filteredLibrary.length === 0 && (
              <div style={{ padding: 16, color: '#94a3b8', fontSize: 12 }}>
                Keine Treffer.
              </div>
            )}
            {/* W1: Section-Cards mit Live-Thumbnail. Die Vorschau wird in
                einer 320px-breiten, auf 30% skalierten Box gerendert — das
                gibt einen ~96-px breiten Mini-Render. Pointer-Events aus,
                der ganze Card-Klick fügt die Section ein. */}
            {filteredLibrary.map((c) => (
              <button
                key={c.slug}
                type="button"
                onClick={() => (swapPanel.mode === 'swap' ? swapBlock(swapPanel.targetIdx, c.slug) : addBlock(c.slug))}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  padding: 0,
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  background: '#fff',
                  marginBottom: 8,
                  cursor: 'pointer',
                  overflow: 'hidden',
                  transition: 'border-color 0.15s, background 0.15s, transform 0.1s',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = KC_MID;
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e2e8f0';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                {/* Live Thumbnail */}
                {c.html_template ? (
                  <div style={{
                    height: 90, overflow: 'hidden',
                    background: '#f8fafc',
                    borderBottom: '1px solid #e2e8f0',
                    position: 'relative',
                  }}>
                    <div style={{
                      width: 1200, transform: 'scale(0.25)', transformOrigin: 'top left',
                      pointerEvents: 'none',
                    }}
                      dangerouslySetInnerHTML={{ __html: c.html_template }}
                    />
                  </div>
                ) : (
                  <div style={{
                    height: 60, background: '#f1f5f9',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#94a3b8', fontSize: 10, fontStyle: 'italic',
                  }}>
                    Keine Vorschau
                  </div>
                )}
                <div style={{ padding: 8 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: KC_DARK, marginBottom: 2 }}>{c.name}</div>
                  <div style={{ fontSize: 9, color: '#64748b', fontFamily: 'ui-monospace, monospace' }}>{c.slug}</div>
                </div>
              </button>
            ))}
          </div>
        </aside>
      )}
    </div>
  );
}

function BlockCard({
  idx, block, libraryEntry,
  isDragOver, isDragging,
  onDragStart, onDragOver, onDrop, onDragEnd,
  onSwap, onRemove,
}) {
  const html = libraryEntry?.html_template || '';
  const name = libraryEntry?.name || block.slug;
  const category = libraryEntry?.category || '—';

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onDragEnd={onDragEnd}
      style={{
        position: 'relative',
        background: '#fff',
        border: isDragOver ? `2px dashed ${KC_MID}` : '1px solid #e2e8f0',
        borderRadius: 8,
        overflow: 'hidden',
        opacity: isDragging ? 0.4 : 1,
        transition: 'opacity 0.1s',
      }}
    >
      {/* Compact-Header — Drag-Handle + Name + Category-Badge + Hover-Actions */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 10px',
          background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          fontSize: 11,
        }}
      >
        <span
          aria-hidden title="Ziehen zum Sortieren"
          style={{ cursor: 'grab', color: '#94a3b8', fontSize: 14, lineHeight: 1, userSelect: 'none' }}
        >⠿</span>
        <span style={{
          background: '#e2e8f0', color: '#475569',
          fontSize: 9, fontWeight: 700,
          padding: '2px 6px', borderRadius: 3,
          textTransform: 'uppercase', letterSpacing: '0.05em',
        }}>{category}</span>
        <span style={{
          flex: 1, minWidth: 0,
          fontSize: 11, fontWeight: 700, color: KC_DARK,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>{name}</span>
        <span style={{ color: '#94a3b8', fontFamily: 'ui-monospace, monospace', fontSize: 10 }}>
          #{idx + 1}
        </span>
        <button
          type="button" onClick={onSwap}
          style={{
            background: 'transparent', color: KC_MID,
            border: `1px solid ${KC_MID}`, borderRadius: 4,
            padding: '2px 8px', fontSize: 10, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >Tauschen</button>
        <button
          type="button" onClick={onRemove} aria-label="Block entfernen"
          style={{
            background: 'transparent', color: '#dc2626',
            border: '1px solid #fca5a5', borderRadius: 4,
            padding: '2px 8px', fontSize: 11, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >✕</button>
      </div>

      {/* Live HTML-Preview — pointerEvents:none damit Klicks im Section-Inhalt
          (Links, Buttons) nicht aktiv sind. Section rendert sich responsiv,
          weil die outer-width vom Preview-Size-Toggle bestimmt wird. */}
      <div
        style={{
          background: '#fff',
          minHeight: 80,
          pointerEvents: 'none',
        }}
      >
        {html ? (
          <div dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontSize: 12, fontStyle: 'italic' }}>
            Keine Vorschau verfügbar (Library-Eintrag fehlt)
          </div>
        )}
      </div>
    </div>
  );
}
