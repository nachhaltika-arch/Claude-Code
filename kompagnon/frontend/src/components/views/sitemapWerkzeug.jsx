/**
 * Werkzeugleiste, Seitenleiste und die Verbindungslinien (L-25).
 *
 * Am 2026-08-30 aus `SitemapViewV2.jsx` herausgeloest — 416 Zeilen.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  GLOBAL_SECTION_KEYS, KC_DARK, KC_MID, SECTION_CATALOG, SECTION_LABEL, SIDEBAR_CATEGORIES,
  btnPrimary, btnSecondary,
} from './sitemapDaten';

export function BottomToolbar({ zoom, onZoomIn, onZoomOut, onZoomReset, pageCount }) {
  return (
    <div style={{
      position: 'absolute',
      bottom: 16, left: '50%',
      transform: 'translateX(-50%)',
      display: 'flex', alignItems: 'center', gap: 6,
      padding: 4,
      background: '#fff',
      border: '1px solid var(--border-light)',
      borderRadius: 10,
      boxShadow: '0 4px 14px rgba(0,0,0,0.08)',
      zIndex: 50,
      fontFamily: 'inherit',
    }}>
      <ToolbarButton onClick={onZoomOut} disabled={zoom <= 0.4} title="Verkleinern (Strg+-)">−</ToolbarButton>
      <button
        type="button" onClick={onZoomReset}
        title="Zoom zuruecksetzen (Strg+0)"
        style={{
          minWidth: 60, padding: '6px 10px',
          background: 'transparent', border: 'none',
          cursor: 'pointer', color: KC_DARK,
          fontSize: 12, fontWeight: 700, fontFamily: 'inherit',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {Math.round(zoom * 100)}%
      </button>
      <ToolbarButton onClick={onZoomIn} disabled={zoom >= 1.5} title="Vergroessern (Strg++)">+</ToolbarButton>
      <div style={{ width: 1, height: 20, background: 'var(--border-light)', margin: '0 4px' }} />
      <span style={{ padding: '6px 10px', fontSize: 12, color: 'var(--text-secondary)', fontWeight: 600 }}>
        {pageCount} {pageCount === 1 ? 'Seite' : 'Seiten'}
      </span>
    </div>
  );
}

export function ToolbarButton({ children, onClick, disabled, title }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled} title={title}
      style={{
        width: 30, height: 30,
        background: 'transparent', border: 'none', borderRadius: 6,
        cursor: disabled ? 'not-allowed' : 'pointer',
        color: disabled ? 'var(--border-medium)' : KC_DARK,
        fontSize: 16, fontWeight: 700, fontFamily: 'inherit',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 0,
      }}
      onMouseEnter={(e) => { if (!disabled) e.currentTarget.style.background = 'var(--surface)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      {children}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase C polish: SVG-Overlay zeichnet Edges fuer interne Links zwischen Pages
// ─────────────────────────────────────────────────────────────────────────────
//
// Liest die DOM-Position jeder PageCard ueber Refs und zeichnet Bezier-Pfade
// von der Quelle (bottom-center) zum Ziel (top-center). Recompute bei jedem
// edgeTick (Resize / Card-Add/Remove / Layout-Change).

export function LinkEdgeOverlay({ tick, cardRefs, canvasInnerRef, linksByPageId }) {
  const [paths, setPaths] = useState([]);

  useEffect(() => {
    if (!canvasInnerRef.current || !linksByPageId) {
      setPaths([]);
      return;
    }
    const canvasRect = canvasInnerRef.current.getBoundingClientRect();
    const newPaths = [];
    linksByPageId.forEach((linkData, fromPageId) => {
      (linkData.internal || []).forEach((link, idx) => {
        if (!link.toPageId || link.toPageId === fromPageId) return;
        const fromNode = cardRefs.get(fromPageId);
        const toNode = cardRefs.get(link.toPageId);
        if (!fromNode || !toNode) return;
        const fr = fromNode.getBoundingClientRect();
        const tr = toNode.getBoundingClientRect();
        // Source: bottom-center of fromCard
        const sx = fr.left + fr.width / 2 - canvasRect.left;
        const sy = fr.bottom - canvasRect.top;
        // Target: top-center of toCard
        const tx = tr.left + tr.width / 2 - canvasRect.left;
        const ty = tr.top - canvasRect.top;
        // Cubic Bezier: kontroll-punkte ziehen die Kurve vertikal nach unten
        // bzw. nach oben — vermeidet ueberlappende Linien bei seitlich
        // platzierten Pages.
        const dy = Math.abs(ty - sy);
        const dx = Math.abs(tx - sx);
        const curvature = Math.min(80, Math.max(30, dy * 0.4 + dx * 0.1));
        const cp1y = sy + curvature;
        const cp2y = ty - curvature;
        const d = `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${sx.toFixed(1)} ${cp1y.toFixed(1)}, ${tx.toFixed(1)} ${cp2y.toFixed(1)}, ${tx.toFixed(1)} ${ty.toFixed(1)}`;
        newPaths.push({
          key: `${fromPageId}-${link.toPageId}-${link.slot}-${idx}`,
          d,
          slot: link.slot,
        });
      });
    });
    setPaths(newPaths);
  }, [tick, linksByPageId, cardRefs, canvasInnerRef]);

  if (paths.length === 0) return null;

  return (
    <svg
      style={{
        position: 'absolute', inset: 0,
        width: '100%', height: '100%',
        pointerEvents: 'none', overflow: 'visible',
        zIndex: 1,
      }}
    >
      <defs>
        <marker
          id="sitemap-link-arrow"
          markerWidth="9" markerHeight="9"
          refX="7" refY="3"
          orient="auto" markerUnits="strokeWidth"
        >
          <path d="M0,0 L0,6 L8,3 z" fill="#2563eb" />
        </marker>
      </defs>
      {paths.map((p) => (
        <path
          key={p.key}
          d={p.d}
          stroke="#2563eb" strokeWidth="1.5"
          fill="none" strokeDasharray="5 4"
          markerEnd="url(#sitemap-link-arrow)"
          opacity="0.55"
        >
          <title>{p.slot}</title>
        </path>
      ))}
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase 2: AddSidebar — links, Search + Global Sections + Categories
// ─────────────────────────────────────────────────────────────────────────────

export function AddSidebar({ pages, activePageId, onAddToActivePage, setDragState, endDrag }) {
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState('');
  // Default: alle Categories collapsed; "Global" ist immer offen.
  const [openCategories, setOpenCategories] = useState({});

  // Instance-Count pro Section-Key — wieviele Pages nutzen sie
  const instanceCount = useMemo(() => {
    const map = new Map();
    pages.forEach((p) => {
      (p.sections || []).forEach((key) => {
        map.set(key, (map.get(key) || 0) + 1);
      });
    });
    return map;
  }, [pages]);

  const matchesSearch = useCallback((key) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    const desc = SECTION_CATALOG[key] || '';
    const label = SECTION_LABEL[key] || key;
    return key.toLowerCase().includes(q)
      || desc.toLowerCase().includes(q)
      || label.toLowerCase().includes(q);
  }, [search]);

  // Wenn Suche aktiv: alle Categories temporaer aufklappen, damit Treffer sichtbar sind
  const isSearching = search.trim().length > 0;

  if (collapsed) {
    return (
      <aside style={{
        width: 36, flexShrink: 0,
        background: '#fff', borderRight: '1px solid var(--border-light)',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: '12px 0',
      }}>
        <button
          type="button" onClick={() => setCollapsed(false)}
          aria-label="Add-Sidebar einblenden"
          title="Add-Sidebar einblenden"
          style={{
            background: 'none', border: 'none',
            color: KC_MID, fontSize: 18, cursor: 'pointer', padding: 4,
          }}
        >
          ➕
        </button>
      </aside>
    );
  }

  return (
    <aside style={{
      width: 280, flexShrink: 0,
      background: '#fff', borderRight: '1px solid var(--border-light)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      fontFamily: 'inherit',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 14px', borderBottom: '1px solid var(--border-light)',
      }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: KC_DARK, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Add
        </div>
        <button type="button" onClick={() => setCollapsed(true)}
          aria-label="Sidebar einklappen" title="Sidebar einklappen"
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 14, padding: 0 }}>
          ×
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: 10, borderBottom: '1px solid var(--border-light)' }}>
        <input aria-label="Suchen…"
          type="search" placeholder="Suchen…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '7px 10px',
            border: '1px solid var(--border-light)', borderRadius: 6,
            fontSize: 12, fontFamily: 'inherit', outline: 'none',
          }}
        />
      </div>

      {/* Scroll-Bereich */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
        {!activePageId && (
          <div style={{
            margin: '0 0 10px',
            padding: '8px 10px', fontSize: 12, color: '#92400e',
            background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 6,
            lineHeight: 1.4,
          }}>
            Tipp: Klick erst auf eine Seite, dann auf eine Section um sie hinzuzufügen.
          </div>
        )}

        {/* Global Sections — immer offen */}
        <div style={{ marginBottom: 12 }}>
          <div style={{
            padding: '4px 6px',
            fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)',
            textTransform: 'uppercase', letterSpacing: '0.08em',
          }}>
            Global Sections
          </div>
          {GLOBAL_SECTION_KEYS.filter(matchesSearch).map((key) => (
            <SidebarSectionItem
              key={key} sectionKey={key}
              count={instanceCount.get(key) || 0}
              global
              onPick={() => onAddToActivePage(key)}
              setDragState={setDragState} endDrag={endDrag}
            />
          ))}
        </div>

        {/* Categories */}
        {SIDEBAR_CATEGORIES.map((cat) => {
          const items = cat.items.filter(matchesSearch);
          if (items.length === 0) return null;
          const isOpen = isSearching || openCategories[cat.label] || false;
          return (
            <div key={cat.label} style={{ marginBottom: 4 }}>
              <button
                type="button"
                onClick={() => setOpenCategories((s) => ({ ...s, [cat.label]: !isOpen }))}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, width: '100%',
                  padding: '8px 10px',
                  background: 'transparent', border: 'none',
                  cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left',
                  borderRadius: 6,
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-app)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ color: 'var(--text-tertiary)', fontSize: 12, flexShrink: 0 }}>
                  {isOpen ? '▼' : '▶'}
                </span>
                <span style={{ fontSize: 12, fontWeight: 700, color: KC_DARK }}>
                  {cat.label}
                </span>
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{items.length}</span>
              </button>
              {isOpen && (
                <div style={{ paddingLeft: 4 }}>
                  {items.map((key) => (
                    <SidebarSectionItem
                      key={key} sectionKey={key}
                      count={instanceCount.get(key) || 0}
                      onPick={() => onAddToActivePage(key)}
                      setDragState={setDragState} endDrag={endDrag}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}

export function SidebarSectionItem({ sectionKey, count, global = false, onPick, setDragState, endDrag }) {
  const label = SECTION_LABEL[sectionKey] || sectionKey;
  const desc = SECTION_CATALOG[sectionKey] || '';

  return (
    <button
      type="button" onClick={onPick}
      draggable={!!setDragState}
      onDragStart={(e) => {
        if (!setDragState) return;
        setDragState({ fromPageId: null, fromIdx: null, sectionKey });
        try { e.dataTransfer.setData('text/plain', sectionKey); } catch (_) {}
        e.dataTransfer.effectAllowed = 'copy';
      }}
      onDragEnd={() => endDrag && endDrag()}
      title={desc}
      style={{
        display: 'flex', alignItems: 'center', gap: 8, width: '100%',
        padding: '6px 8px', marginBottom: 2,
        background: global ? '#ecfdf5' : 'transparent',
        border: '1px solid transparent', borderRadius: 6,
        cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left',
        fontSize: 12,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = global ? '#d1fae5' : '#eff6ff';
        e.currentTarget.style.borderColor = KC_MID;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = global ? '#ecfdf5' : 'transparent';
        e.currentTarget.style.borderColor = 'transparent';
      }}
    >
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: global ? '#10b981' : 'var(--border-medium)', flexShrink: 0,
      }} />
      <span style={{
        flex: 1, minWidth: 0,
        fontWeight: 600, color: KC_DARK,
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}>
        {label}
      </span>
      {count > 0 && (
        <span style={{
          fontSize: 9, fontWeight: 700,
          padding: '1px 6px', borderRadius: 10,
          background: 'var(--surface)', color: 'var(--text-secondary)',
          flexShrink: 0,
        }}>
          {count}
        </span>
      )}
      <span style={{ color: KC_MID, fontSize: 13, lineHeight: 1, flexShrink: 0 }}>+</span>
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// EmptyState
// ─────────────────────────────────────────────────────────────────────────────

export function EmptyState({ onAddPage, onRegenerateSitemap }) {
  return (
    <div style={{
      maxWidth: 480, margin: '60px auto',
      border: '2px dashed var(--border-medium)', borderRadius: 16, padding: 40,
      textAlign: 'center', color: 'var(--text-secondary)', background: '#fff',
    }}>
      <div style={{ fontSize: 36, marginBottom: 8 }}>🗺</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: KC_DARK, marginBottom: 8 }}>
        Noch keine Sitemap-Seiten
      </div>
      <div style={{ fontSize: 13, marginBottom: 20 }}>
        Lege manuell Seiten an oder lass die KI eine Struktur vorschlagen.
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
        <button type="button" onClick={onAddPage} style={btnSecondary}>
          + Erste Seite
        </button>
        <button type="button" onClick={() => onRegenerateSitemap?.(0)} style={btnPrimary}>
          ⚡ KI-Vorschlag
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Side-Panel: Page-Details (Name / Type / Status / KI-Prompt)
// ─────────────────────────────────────────────────────────────────────────────

