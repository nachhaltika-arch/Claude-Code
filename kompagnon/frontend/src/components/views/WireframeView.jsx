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

// W3: ersetzt {{key}}-Marker im html_template durch slot-Werte (HTML-escaped).
// Wird in BlockCard's Live-Preview angewendet — User sieht seine Edits sofort.
function renderSlots(html, slotValues) {
  if (!html) return '';
  if (!slotValues || typeof slotValues !== 'object') return html;
  const escape = (s) => String(s).replace(/[<>&"']/g, (c) => (
    { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' }[c]
  ));
  let result = html;
  Object.entries(slotValues).forEach(([key, value]) => {
    if (value == null) return;
    const re = new RegExp(`\\{\\{\\s*${key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\}\\}`, 'g');
    result = result.replace(re, escape(value));
  });
  return result;
}

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
  // W3 Slot-Editor: { idx } oder null
  const [editPanel, setEditPanel] = useState(null);

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

  // W2: Empfohlen-Top-3 für den aktuellen Slot. Basis:
  //  - swap-Mode → gleiche Kategorie wie der zu tauschende Block, exkl. selbst & existierende
  //  - add-Mode  → noch-nicht-verwendete Library-Items
  // Nicht durch Filter / Suche beeinflusst — bleibt bewusst above-fold sichtbar.
  const recommendations = useMemo(() => {
    if (!swapPanel.open || library.length === 0) return [];
    const usedSlugs = new Set(activeBlocks.map((b) => b.slug));
    if (swapPanel.mode === 'swap') {
      const target = activeBlocks[swapPanel.targetIdx];
      if (!target) return [];
      const targetEntry = library.find((c) => c.slug === target.slug);
      if (!targetEntry) return [];
      return library
        .filter((c) => c.category === targetEntry.category && c.slug !== target.slug && !usedSlugs.has(c.slug))
        .slice(0, 3);
    }
    return library.filter((c) => !usedSlugs.has(c.slug)).slice(0, 3);
  }, [swapPanel.open, swapPanel.mode, swapPanel.targetIdx, library, activeBlocks]);

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

  // W2: KI-Variation — fragt Backend nach Alternativ-Block gleicher Kategorie
  // und tauscht den aktuellen Block dadurch aus. Other Blocks der Page werden
  // als exclude_slugs mitgegeben, damit kein Duplikat vorgeschlagen wird.
  const requestVariation = async (targetIdx) => {
    if (!activePage) return;
    const current = activeBlocks[targetIdx];
    if (!current) return;
    try {
      const otherSlugs = activeBlocks
        .filter((_, i) => i !== targetIdx)
        .map((b) => b.slug);
      const res = await fetch(`${API_BASE_URL}/api/components/variation`, {
        method: 'POST', headers,
        body: JSON.stringify({
          current_slug:  current.slug,
          exclude_slugs: otherSlugs,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const msg = typeof detail === 'string' ? detail : `Fehler ${res.status}`;
        // eslint-disable-next-line no-console
        console.warn('variation failed:', msg);
        return;
      }
      // Library-Cache mit dem neuen Eintrag aktualisieren falls der noch nicht drin
      // (sollte er aber sein — eager-Load am Mount).
      if (body?.slug && !library.find((c) => c.slug === body.slug)) {
        setLibrary((prev) => [...prev, body]);
      }
      swapBlock(targetIdx, body.slug);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.warn('variation request failed:', e);
    }
  };

  // W3: Slot-Werte eines Blocks updaten + persistieren.
  const updateBlockSlots = (targetIdx, nextSlots) => {
    if (!activePage) return;
    const nextBlocks = activeBlocks.map((b, i) =>
      i === targetIdx ? { ...b, slots: nextSlots } : b,
    );
    const nextData = {
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
  };

  // W3: Block-HTML als neuer Custom-Library-Eintrag speichern. Antwort enthält
  // den neuen ComponentLibrary-Eintrag — wir cachen ihn lokal und tauschen den
  // Block der aktuellen Page auf den neuen Slug aus.
  const saveAsCustom = async (targetIdx, payload) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/components/save-custom`, {
        method: 'POST', headers,
        body: JSON.stringify(payload),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const msg = typeof detail === 'string' ? detail : `Fehler ${res.status}`;
        throw new Error(msg);
      }
      // Library-Cache erweitern + Block auf neuen Slug umstellen
      setLibrary((prev) => [...prev, body]);
      swapBlock(targetIdx, body.slug);
      return body;
    } catch (e) {
      // eslint-disable-next-line no-console
      console.warn('save-custom failed:', e);
      return null;
    }
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
                onVariation={() => requestVariation(idx)}
                onEdit={() => setEditPanel({ idx })}
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

      {/* W3: Slot-Editor-Modal */}
      {editPanel && (() => {
        const target = activeBlocks[editPanel.idx];
        const lib = target ? library.find((c) => c.slug === target.slug) : null;
        if (!target) return null;
        return (
          <SlotEditorModal
            block={target}
            libraryEntry={lib}
            onClose={() => setEditPanel(null)}
            onSaveSlots={(values) => {
              updateBlockSlots(editPanel.idx, values);
              setEditPanel(null);
            }}
            onSaveAsCustom={async (payload) => {
              const created = await saveAsCustom(editPanel.idx, payload);
              if (created) setEditPanel(null);
            }}
          />
        );
      })()}

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
            {/* W2: „Empfohlen für diesen Slot" — Top-3 Vorschläge.
                Sichtbar nur wenn keine User-Filter aktiv (Default-Zustand),
                damit gefilterte Suche nicht durch eine Empfehlungs-Liste
                verwirrt wird. */}
            {recommendations.length > 0 && !searchQuery && activeCategory === 'Alle' && (
              <div style={{
                marginBottom: 12, padding: 8,
                background: '#FEF3C7', border: '1px solid #FCD34D',
                borderRadius: 8,
              }}>
                <div style={{
                  fontSize: 10, fontWeight: 800, color: '#92400E',
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                  marginBottom: 6, padding: '0 2px',
                }}>
                  💡 Empfohlen für diesen Slot
                </div>
                {recommendations.map((c) => (
                  <LibraryCard
                    key={`rec-${c.slug}`}
                    item={c}
                    onPick={() => (swapPanel.mode === 'swap' ? swapBlock(swapPanel.targetIdx, c.slug) : addBlock(c.slug))}
                    compact
                  />
                ))}
              </div>
            )}

            {filteredLibrary.map((c) => (
              <LibraryCard
                key={c.slug}
                item={c}
                onPick={() => (swapPanel.mode === 'swap' ? swapBlock(swapPanel.targetIdx, c.slug) : addBlock(c.slug))}
              />
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
  onSwap, onVariation, onEdit, onRemove,
}) {
  // W3: Slot-Werte aus dem Block in die Live-Preview einrendern
  const html = renderSlots(libraryEntry?.html_template || '', block?.slots);
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
          type="button" onClick={onEdit}
          title="Slots editieren / als Custom speichern"
          style={{
            background: 'transparent', color: KC_DARK,
            border: `1px solid ${KC_DARK}`, borderRadius: 4,
            padding: '2px 8px', fontSize: 10, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >✏️ Edit</button>
        <button
          type="button" onClick={onVariation}
          title="Variante aus gleicher Kategorie vorschlagen"
          style={{
            background: '#7c3aed', color: '#fff',
            border: 'none', borderRadius: 4,
            padding: '3px 8px', fontSize: 10, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >🔄 Variante</button>
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

// ── W2: Library-Card (wiederverwendbar — auch in der "Empfohlen"-Sektion) ─────

function LibraryCard({ item, onPick, compact = false }) {
  const thumbHeight = compact ? 70 : 90;
  return (
    <button
      type="button"
      onClick={onPick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: 0,
        border: '1px solid #e2e8f0',
        borderRadius: 8,
        background: '#fff',
        marginBottom: compact ? 6 : 8,
        cursor: 'pointer',
        overflow: 'hidden',
        transition: 'border-color 0.15s, transform 0.1s',
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
      {item.html_template ? (
        <div style={{
          height: thumbHeight, overflow: 'hidden',
          background: '#f8fafc',
          borderBottom: '1px solid #e2e8f0',
          position: 'relative',
        }}>
          <div style={{
            width: 1200, transform: 'scale(0.25)', transformOrigin: 'top left',
            pointerEvents: 'none',
          }}
            dangerouslySetInnerHTML={{ __html: item.html_template }}
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
      <div style={{ padding: compact ? '6px 8px' : 8 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: KC_DARK, marginBottom: 2 }}>{item.name}</div>
        <div style={{ fontSize: 9, color: '#64748b', fontFamily: 'ui-monospace, monospace' }}>{item.slug}</div>
      </div>
    </button>
  );
}

// ── W3: Slot-Editor-Modal ─────────────────────────────────────────────────────

function SlotEditorModal({ block, libraryEntry, onClose, onSaveSlots, onSaveAsCustom }) {
  const slots = libraryEntry?.slots || [];
  const html  = libraryEntry?.html_template || '';
  const [values, setValues] = useState(() => {
    const init = {};
    slots.forEach((s) => {
      init[s.key] = (block?.slots && block.slots[s.key]) ?? s.default ?? '';
    });
    return init;
  });
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customSlug, setCustomSlug] = useState(`${block.slug}-custom`);
  const [customName, setCustomName] = useState(libraryEntry?.name ? `${libraryEntry.name} (Custom)` : 'Custom Section');
  const [showRawHtml, setShowRawHtml] = useState(false);
  const [rawHtml, setRawHtml] = useState(html);
  const [saving, setSaving] = useState(false);

  const previewHtml = useMemo(() => {
    const baseHtml = showRawHtml ? rawHtml : html;
    return renderSlots(baseHtml, values);
  }, [html, rawHtml, values, showRawHtml]);

  const hasSlots = slots.length > 0;

  const handleSlotSave = () => {
    if (saving) return;
    setSaving(true);
    onSaveSlots(values);
  };

  const handleCustomSave = async () => {
    if (saving) return;
    setSaving(true);
    await onSaveAsCustom({
      new_slug:       customSlug.trim().toLowerCase(),
      new_name:       customName.trim(),
      html_template:  showRawHtml ? rawHtml : renderSlots(html, values),
      category:       libraryEntry?.category || 'CUSTOM',
      source_slug:    block.slug,
      slots:          showRawHtml ? [] : (libraryEntry?.slots || []),
      ki_prompt_hint: libraryEntry?.ki_prompt_hint || '',
      preview_note:   `Custom-Variante von ${libraryEntry?.name || block.slug}`,
    });
    setSaving(false);
  };

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 12,
        width: '100%', maxWidth: 920, maxHeight: 'calc(100vh - 32px)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      }}>
        {/* Header */}
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: '#f8fafc',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, color: KC_DARK }}>
              {libraryEntry?.name || block.slug}
            </div>
            <div style={{ fontSize: 11, color: '#64748b', fontFamily: 'ui-monospace, monospace' }}>
              {block.slug}
            </div>
          </div>
          <button type="button" onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#64748b', lineHeight: 1 }}>×</button>
        </div>

        {/* Body: 2-Spalten — Form links, Live-Preview rechts */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Form */}
          <div style={{ flex: '0 0 360px', padding: 16, overflowY: 'auto', borderRight: '1px solid #e2e8f0' }}>
            {!hasSlots && !showRawHtml && (
              <div style={{
                padding: 12, fontSize: 12, color: '#92400e',
                background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 6,
                marginBottom: 12,
              }}>
                Diese Section hat keine definierten Slots. Klick „HTML direkt bearbeiten" für volle Kontrolle.
              </div>
            )}

            {hasSlots && !showRawHtml && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {slots.map((s) => (
                  <div key={s.key}>
                    <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 3 }}>
                      {s.label || s.key}
                    </label>
                    <input
                      type="text"
                      value={values[s.key] ?? ''}
                      onChange={(e) => setValues((v) => ({ ...v, [s.key]: e.target.value }))}
                      placeholder={s.default || ''}
                      style={{ width: '100%', boxSizing: 'border-box', padding: '7px 10px', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 12, fontFamily: 'inherit' }}
                    />
                    <div style={{ fontSize: 9, color: '#94a3b8', marginTop: 2, fontFamily: 'ui-monospace, monospace' }}>
                      {`{{${s.key}}}`}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showRawHtml && (
              <div>
                <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4 }}>
                  HTML-Template (Tailwind)
                </label>
                <textarea
                  value={rawHtml}
                  onChange={(e) => setRawHtml(e.target.value)}
                  rows={20}
                  style={{ width: '100%', boxSizing: 'border-box', padding: 10, border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 11, fontFamily: 'ui-monospace, monospace', resize: 'vertical' }}
                />
                <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 4 }}>
                  Änderungen werden nur sichtbar wenn du als Custom-Section speicherst.
                </div>
              </div>
            )}

            <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px dashed #e2e8f0' }}>
              <button type="button"
                onClick={() => setShowRawHtml((v) => !v)}
                style={{ background: 'none', border: 'none', color: KC_MID, fontSize: 11, fontWeight: 700, cursor: 'pointer', padding: 0 }}>
                {showRawHtml ? '← Slot-Modus' : 'HTML direkt bearbeiten →'}
              </button>
            </div>

            {showCustomForm && (
              <div style={{ marginTop: 14, padding: 10, background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 6, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: '#92400e', marginBottom: 3 }}>Custom-Slug</label>
                  <input value={customSlug} onChange={(e) => setCustomSlug(e.target.value)}
                    style={{ width: '100%', boxSizing: 'border-box', padding: '6px 8px', border: '1px solid #FCD34D', borderRadius: 4, fontSize: 11, fontFamily: 'ui-monospace, monospace' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 10, fontWeight: 700, color: '#92400e', marginBottom: 3 }}>Anzeigename</label>
                  <input value={customName} onChange={(e) => setCustomName(e.target.value)}
                    style={{ width: '100%', boxSizing: 'border-box', padding: '6px 8px', border: '1px solid #FCD34D', borderRadius: 4, fontSize: 11 }} />
                </div>
              </div>
            )}
          </div>

          {/* Live-Preview rechts */}
          <div style={{ flex: 1, overflow: 'auto', background: '#f8fafc', padding: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
              Live-Preview
            </div>
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden', pointerEvents: 'none' }}>
              {previewHtml ? (
                <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
              ) : (
                <div style={{ padding: 32, textAlign: 'center', color: '#94a3b8', fontSize: 12 }}>Keine Vorschau</div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px 18px', borderTop: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', gap: 8,
          background: '#f8fafc',
        }}>
          <button type="button" onClick={() => setShowCustomForm((v) => !v)}
            style={{ padding: '8px 14px', background: '#fff', border: `1px solid ${KC_MID}`, color: KC_MID, borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
            {showCustomForm ? '× Custom abbrechen' : '💾 Als Custom-Section speichern'}
          </button>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" onClick={onClose} disabled={saving}
              style={{ padding: '8px 14px', background: '#fff', border: '1px solid #cbd5e1', color: '#64748b', borderRadius: 6, fontSize: 12, cursor: 'pointer' }}>
              Abbrechen
            </button>
            {showCustomForm ? (
              <button type="button" onClick={handleCustomSave} disabled={saving || !customSlug.trim() || !customName.trim()}
                style={{ padding: '8px 18px', background: saving ? '#94a3b8' : KC_MID, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: saving ? 'wait' : 'pointer' }}>
                {saving ? 'Speichert…' : '✓ Custom speichern + anwenden'}
              </button>
            ) : (
              <button type="button" onClick={handleSlotSave} disabled={saving || (!hasSlots && !showRawHtml)}
                style={{ padding: '8px 18px', background: saving || (!hasSlots && !showRawHtml) ? '#94a3b8' : KC_DARK, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: saving ? 'wait' : 'pointer' }}>
                {saving ? 'Speichert…' : '✓ Slots speichern'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
