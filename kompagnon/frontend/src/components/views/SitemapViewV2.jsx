/**
 * SitemapViewV2 — Phase 1 des Relume-Style-Sitemap-Rebuilds.
 *
 * Layout:
 *   - Horizontale Anordnung der Pages, Tree-Connectors fuer Hierarchie
 *   - Page-Karten zeigen die ganze Section-Liste inline (mit Description)
 *   - "+" zwischen Pages (sibling) und zwischen Sections (add)
 *   - "..." Context-Menu pro Page mit Aktionen (Duplicate / Delete / etc.)
 *
 * Phase 2 ergaenzt eine linke Add-Sidebar.
 * Phase 3 ergaenzt Drag-and-Drop fuer Sections.
 * Phase 4 ergaenzt Page-Groups (eltern → wiederholte Kinder mit shared sections).
 *
 * Backend-Endpoints (alle existierend in routers/sitemap.py):
 *   GET    /api/sitemap/{leadId}              — pages laden
 *   POST   /api/sitemap/{leadId}/pages        — Page anlegen
 *   PUT    /api/sitemap/pages/{id}            — Page-Details aktualisieren (incl sections)
 *   DELETE /api/sitemap/pages/{id}            — Page loeschen (Pflichtseiten geblockt)
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';
// Am 30.08.2026 herausgeloest (L-25): Die Datei trug 2.210 Zeilen und darin
// siebzehn Unterkomponenten. Sie waren dort schon eigene Funktionen.
import {
  KC_DARK, COL_GAP, SECTION_CATALOG, slugify, isUrlSlot, isExternalUrl, matchInternalPage, btnPrimary, btnSecondary, btnTeal,
} from './sitemapDaten';
import { PageColumn, AddPagePlus } from './sitemapKarten';
import {
  AddSidebar, BottomToolbar, EmptyState, LinkEdgeOverlay,
} from './sitemapWerkzeug';
import {
  AddPageDialog, AddSectionDialog, PageDetailPanel,
} from './sitemapDialoge';

export default function SitemapViewV2({
  projectId,
  leadId,
  wireframeData,
  onGenerateWireframe,
  onNavigateToWireframe,
  onRegenerateSitemap,
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPageId, setSelectedPageId] = useState(null);
  const [addPageState, setAddPageState] = useState(null);   // null | { parent_id, position }
  const [addSectionState, setAddSectionState] = useState(null); // null | { page_id, position }

  // Phase 3: DnD-State fuer Section-Reorder + Cross-Page-Move + Sidebar-Drop
  // dragState: { fromPageId|null, fromIdx|null, sectionKey } — null wenn nichts gezogen wird.
  // fromPageId=null bedeutet: Drag aus der Add-Sidebar (Quelle ist die Library, kein Origin-Page).
  const [dragState, setDragState] = useState(null);
  // dropTarget signalisiert dem aktuell ueberfahrenen DropZone, dass er hervorgehoben wird.
  // { pageId, position } | null
  const [dropTarget, setDropTarget] = useState(null);

  // Phase C polish: Card-DOM-Refs fuer SVG-Link-Edges. Map<pageId, HTMLElement>.
  // Mutable Ref + Tick-State, weil Refs allein keine Re-Renders triggern.
  const cardRefs = useRef(new Map());
  const canvasInnerRef = useRef(null);
  const [edgeTick, setEdgeTick] = useState(0);
  // Phase D: Zoom-Level fuer das Sitemap-Canvas. 1.0 = 100%, 0.5 = 50% (Vogelperspektive).
  const [zoom, setZoom] = useState(1.0);
  const setCardRef = useCallback((pageId, node) => {
    if (node) cardRefs.current.set(pageId, node);
    else cardRefs.current.delete(pageId);
    // RAF damit Layout sich erst stabilisiert
    requestAnimationFrame(() => setEdgeTick((t) => t + 1));
  }, []);

  // Pages laden
  const loadPages = useCallback(() => {
    if (!leadId) return;
    setLoading(true);
    setError('');
    fetch(`${API_BASE_URL}/api/sitemap/${leadId}`, { headers })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data) => setPages(Array.isArray(data) ? data : data.pages || []))
      .catch((e) => setError(e.message || 'Sitemap konnte nicht geladen werden'))
      .finally(() => setLoading(false));
  }, [leadId, headers]);

  useEffect(() => { loadPages(); }, [loadPages]);

  // Phase C polish: Edge-Refresh bei Resize / Pages-Aenderung
  useEffect(() => {
    if (!canvasInnerRef.current) return;
    const obs = new ResizeObserver(() => setEdgeTick((t) => t + 1));
    obs.observe(canvasInnerRef.current);
    return () => obs.disconnect();
  }, []);

  // Phase D: Zoom-Shortcuts (Strg+/-/0). Ignoriert Inputs/Textareas.
  useEffect(() => {
    const handler = (e) => {
      if (!e.ctrlKey && !e.metaKey) return;
      const tag = e.target?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        setZoom((z) => Math.min(1.5, +(z + 0.1).toFixed(2)));
      } else if (e.key === '-') {
        e.preventDefault();
        setZoom((z) => Math.max(0.4, +(z - 0.1).toFixed(2)));
      } else if (e.key === '0') {
        e.preventDefault();
        setZoom(1.0);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // ── Mutationen ────────────────────────────────────────────────────────────

  const savePageDetails = useCallback(async (pageId, updates) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${pageId}`, {
        method: 'PUT', headers,
        body: JSON.stringify(updates),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        throw new Error(typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`);
      }
      const fresh = await res.json();
      setPages((prev) => prev.map((p) => (p.id === pageId ? fresh : p)));
      toast.success('Gespeichert');
      return fresh;
    } catch (e) {
      toast.error(`Speichern fehlgeschlagen: ${e.message}`);
      return null;
    }
  }, [headers]);

  const createPage = useCallback(async (parentId, name, pageType, position) => {
    if (!leadId || !name?.trim()) return null;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
        method: 'POST', headers,
        body: JSON.stringify({
          page_name: name.trim(),
          page_type: pageType || 'info',
          parent_id: parentId || null,
          position: position ?? pages.length,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      const created = await res.json();
      toast.success(`„${created.page_name}" angelegt`);
      loadPages();
      return created;
    } catch (e) {
      toast.error(`Anlegen fehlgeschlagen: ${e.message}`);
      return null;
    }
  }, [leadId, headers, pages.length, loadPages]);

  const deletePage = useCallback(async (pageId) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können nicht gelöscht werden.');
      return;
    }
    if (!window.confirm(`„${target.page_name}" wirklich löschen?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${pageId}`, {
        method: 'DELETE', headers,
      });
      if (!res.ok && res.status !== 204) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      toast.success(`„${target.page_name}" gelöscht`);
      if (selectedPageId === pageId) setSelectedPageId(null);
      loadPages();
    } catch (e) {
      toast.error(`Löschen fehlgeschlagen: ${e.message}`);
    }
  }, [headers, pages, selectedPageId, loadPages]);

  // Duplicate = Page anlegen mit identischen Sections + selber Eltern
  const duplicatePage = useCallback(async (pageId) => {
    const src = pages.find((p) => p.id === pageId);
    if (!src) return;
    const dup = await createPage(src.parent_id, `${src.page_name} (Kopie)`, src.page_type, pages.length);
    if (dup && Array.isArray(src.sections) && src.sections.length > 0) {
      // Sections kopieren — Backend akzeptiert sections im PUT
      await savePageDetails(dup.id, { sections: src.sections });
    }
  }, [pages, createPage, savePageDetails]);

  const addSectionToPage = useCallback((pageId, sectionKey, position) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    if (!sectionKey || !SECTION_CATALOG[sectionKey]) return;
    const next = Array.isArray(target.sections) ? [...target.sections] : [];
    const insertAt = typeof position === 'number' ? position : next.length;
    next.splice(insertAt, 0, sectionKey);
    savePageDetails(pageId, { sections: next });
  }, [pages, savePageDetails]);

  const removeSectionFromPage = useCallback((pageId, idx) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    const next = (target.sections || []).filter((_, i) => i !== idx);
    savePageDetails(pageId, { sections: next });
  }, [pages, savePageDetails]);

  // Phase 3: Section verschieben — within-page reorder + cross-page move +
  // drop-from-sidebar. Bei cross-page macht das zwei PUTs nacheinander.
  // Optimistisches Local-Update damit das UI sofort reagiert; loadPages am
  // Ende nicht noetig (savePageDetails patcht den State).
  const moveSection = useCallback(async ({ fromPageId, fromIdx, toPageId, toIdx, sectionKey }) => {
    if (!toPageId) return;
    const dst = pages.find((p) => p.id === toPageId);
    if (!dst) return;

    // Source kann null sein (Sidebar-Drop) — dann nur Insert in Destination.
    if (fromPageId == null) {
      const next = [...(dst.sections || [])];
      const insertAt = Math.max(0, Math.min(toIdx, next.length));
      next.splice(insertAt, 0, sectionKey);
      await savePageDetails(toPageId, { sections: next });
      return;
    }

    if (fromPageId === toPageId) {
      // Within-page reorder
      const arr = [...(dst.sections || [])];
      if (fromIdx == null || fromIdx < 0 || fromIdx >= arr.length) return;
      const [moved] = arr.splice(fromIdx, 1);
      // Insert-Index korrigieren wenn wir vor der Quelle landen, nach dem Splice
      // hat sich der Index verschoben.
      const insertAt = toIdx > fromIdx ? toIdx - 1 : toIdx;
      arr.splice(Math.max(0, Math.min(insertAt, arr.length)), 0, moved);
      await savePageDetails(toPageId, { sections: arr });
      return;
    }

    // Cross-page: aus Source entfernen + in Destination einfuegen
    const src = pages.find((p) => p.id === fromPageId);
    if (!src) return;
    const sourceArr = (src.sections || []).filter((_, i) => i !== fromIdx);
    const dstArr = [...(dst.sections || [])];
    const insertAt = Math.max(0, Math.min(toIdx, dstArr.length));
    dstArr.splice(insertAt, 0, sectionKey);
    // Sequentiell: erst source, dann destination (verhindert Race wo dst-Save
    // mit alten src-Daten ueberlaeuft).
    await savePageDetails(fromPageId, { sections: sourceArr });
    await savePageDetails(toPageId, { sections: dstArr });
  }, [pages, savePageDetails]);

  const endDrag = useCallback(() => {
    setDragState(null);
    setDropTarget(null);
  }, []);

  // Phase 4: Page-Groups. Eine Page wird zu einer Gruppe gemacht:
  //   - is_group → true
  //   - sections → group_template_sections (Inhalt wandert, Sections selbst leer)
  // Beim Zuruecksetzen das Umgekehrte. Children der Gruppe zeigen das
  // group_template_sections automatisch (Visual nur, nichts in der DB ueberschreiben).
  const toggleGroup = useCallback(async (pageId) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können keine Gruppen werden.');
      return;
    }
    if (!target.is_group) {
      // Zur Gruppe machen — bestehende Sections werden Template
      await savePageDetails(pageId, {
        is_group: true,
        group_template_sections: target.sections || [],
        sections: [],
      });
    } else {
      // Zurueck zu normaler Page — Template wieder in Sections
      await savePageDetails(pageId, {
        is_group: false,
        group_template_sections: [],
        sections: target.group_template_sections || [],
      });
    }
  }, [pages, savePageDetails]);

  // ── Tree-Struktur: Pages nach parent_id gruppieren ────────────────────────

  const tree = useMemo(() => {
    const byParent = new Map();
    pages.forEach((p) => {
      const key = p.parent_id ?? 'root';
      if (!byParent.has(key)) byParent.set(key, []);
      byParent.get(key).push(p);
    });
    // Innerhalb einer Ebene nach position sortieren
    byParent.forEach((arr) => arr.sort((a, b) => (a.position ?? 0) - (b.position ?? 0)));
    return byParent;
  }, [pages]);

  const topLevelPages = tree.get('root') || [];

  const blocksByPageId = useMemo(() => {
    const map = new Map();
    (wireframeData?.pages || []).forEach((p) => {
      map.set(p.page_id, p.blocks || []);
    });
    return map;
  }, [wireframeData]);

  // Phase C: Link-Map pro Page — zeigt Abhaengigkeiten in der Navigation an.
  // Schluessel: page_id; Wert: { internal: [{toPageId, slot, value}], external: [{url, slot}] }
  // Die Slug-Map nutzt das slugified page_name als Schluessel.
  const linksByPageId = useMemo(() => {
    const slugMap = new Map();
    pages.forEach((p) => {
      const s = slugify(p.page_name);
      if (s) slugMap.set(s, p.id);
    });
    const result = new Map();
    (wireframeData?.pages || []).forEach((wp) => {
      const internal = [];
      const external = [];
      (wp.blocks || []).forEach((block) => {
        Object.entries(block.slots || {}).forEach(([key, value]) => {
          if (!isUrlSlot(key, value)) return;
          if (isExternalUrl(value)) {
            // Externe URLs koennten trotzdem auf die eigene Domain zeigen — wenn
            // matchInternalPage was zurueckgibt, behandeln wir es als intern.
            const mapped = matchInternalPage(value, slugMap);
            if (mapped) {
              internal.push({ toPageId: mapped, slot: key, value });
            } else {
              external.push({ url: value, slot: key });
            }
          } else {
            const mapped = matchInternalPage(value, slugMap);
            if (mapped) {
              internal.push({ toPageId: mapped, slot: key, value });
            } else if (value && !value.startsWith('#')) {
              // Unauflösbarer interner Pfad — als external mit Hinweis "unbekannt"
              external.push({ url: value, slot: key, unresolved: true });
            }
          }
        });
      });
      result.set(wp.page_id, { internal, external });
    });
    return result;
  }, [pages, wireframeData]);

  const totalBlocks = (wireframeData?.pages || []).reduce(
    (sum, p) => sum + (p.blocks?.length || 0), 0,
  );

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%', fontFamily: 'var(--font-sans, system-ui)',
      background: 'var(--bg-app)',
    }}>
      {/* Topbar */}
      <div style={{
        flexShrink: 0,
        padding: '14px 24px',
        background: '#fff',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        gap: 16, flexWrap: 'wrap',
      }}>
        <div>
          <h1 style={{
            fontSize: 20, fontWeight: 900, color: KC_DARK, margin: 0,
            textTransform: 'uppercase', letterSpacing: '-0.02em',
          }}>
            Sitemap
          </h1>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
            {pages.length} Seite{pages.length === 1 ? '' : 'n'} ·
            {' '}{totalBlocks} Block{totalBlocks === 1 ? '' : 's'} im Wireframe
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => setAddPageState({ parent_id: null, position: pages.length })}
            style={btnSecondary}
          >
            + Neue Seite
          </button>
          <button
            type="button"
            onClick={() => onRegenerateSitemap?.(0)}
            style={btnSecondary}
          >
            🔄 Sitemap regenerieren
          </button>
          <button
            type="button"
            onClick={onGenerateWireframe} disabled={pages.length === 0}
            style={{
              ...btnPrimary,
              cursor: pages.length === 0 ? 'not-allowed' : 'pointer',
              opacity: pages.length === 0 ? 0.5 : 1,
            }}
          >
            ⚡ KI-Wireframe erzeugen
          </button>
          <button
            type="button" onClick={onNavigateToWireframe} disabled={totalBlocks === 0}
            style={{
              ...btnTeal,
              cursor: totalBlocks === 0 ? 'not-allowed' : 'pointer',
              opacity: totalBlocks === 0 ? 0.5 : 1,
            }}
          >
            Zu Wireframe →
          </button>
        </div>
      </div>

      {/* Canvas + Sidebars */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden', position: 'relative' }}>
        {/* Phase 2: Linke Add-Sidebar — Sections per Klick zur active-Page hinzufuegen.
            Phase 3: Sections koennen alternativ per Drag-and-Drop in eine Page droppen
            (Quelle: fromPageId=null, Ziel: beliebige DropZone). */}
        <AddSidebar
          pages={pages}
          activePageId={selectedPageId}
          onAddToActivePage={(sectionKey) => {
            if (!selectedPageId) {
              toast('Wähle erst eine Seite aus, bevor du eine Section hinzufügst.');
              return;
            }
            addSectionToPage(selectedPageId, sectionKey);
          }}
          setDragState={setDragState}
          endDrag={endDrag}
        />

        <div style={{
          flex: 1, overflow: 'auto',
          padding: '40px 24px',
        }}>
          {loading && <div style={{ color: 'var(--text-secondary)' }}>Sitemap wird geladen…</div>}
          {error && (
            <div style={{ background: '#FEF2F2', color: '#991B1B', padding: 12, borderRadius: 8, fontSize: 13 }}>
              {error}
            </div>
          )}

          {!loading && !error && pages.length === 0 && (
            <EmptyState
              onAddPage={() => setAddPageState({ parent_id: null, position: 0 })}
              onRegenerateSitemap={onRegenerateSitemap}
            />
          )}

          {!loading && !error && pages.length > 0 && (
            <div ref={canvasInnerRef} style={{
              display: 'flex', alignItems: 'flex-start',
              gap: COL_GAP / 2, minWidth: 'max-content',
              position: 'relative',
              transform: `scale(${zoom})`,
              transformOrigin: 'top left',
              transition: 'transform 0.15s ease-out',
            }}>
              {topLevelPages.map((p, idx) => (
                <PageColumn
                  key={p.id}
                  page={p} tree={tree}
                  selectedPageId={selectedPageId}
                  onSelect={setSelectedPageId}
                  onAddSibling={(afterPosition) => setAddPageState({ parent_id: null, position: afterPosition })}
                  onAddChild={(parentId) => setAddPageState({ parent_id: parentId, position: 0 })}
                  onDelete={deletePage}
                  onDuplicate={duplicatePage}
                  onAddSection={(pageId, position) => setAddSectionState({ page_id: pageId, position })}
                  onRemoveSection={removeSectionFromPage}
                  onToggleGroup={toggleGroup}
                  isFirstSibling={idx === 0}
                  dragState={dragState}
                  setDragState={setDragState}
                  dropTarget={dropTarget}
                  setDropTarget={setDropTarget}
                  moveSection={moveSection}
                  endDrag={endDrag}
                  linksByPageId={linksByPageId}
                  pages={pages}
                  setCardRef={setCardRef}
                />
              ))}
              {/* "+" am rechten Ende: neue Top-Level-Seite */}
              <AddPagePlus
                onClick={() => setAddPageState({ parent_id: null, position: pages.length })}
                large
              />
              {/* Phase C polish: SVG-Edges fuer interne Links zwischen Pages */}
              <LinkEdgeOverlay
                tick={edgeTick}
                cardRefs={cardRefs.current}
                canvasInnerRef={canvasInnerRef}
                linksByPageId={linksByPageId}
              />
            </div>
          )}
        </div>

        {/* Side-Panel: Page-Details */}
        {selectedPageId && (
          <PageDetailPanel
            page={pages.find((p) => p.id === selectedPageId) || null}
            onClose={() => setSelectedPageId(null)}
            onSave={(updates) => savePageDetails(selectedPageId, updates)}
            onDelete={() => deletePage(selectedPageId)}
          />
        )}

        {/* Phase D: Bottom-Toolbar mit Zoom-Controls */}
        {!loading && !error && pages.length > 0 && (
          <BottomToolbar
            zoom={zoom}
            onZoomIn={() => setZoom((z) => Math.min(1.5, +(z + 0.1).toFixed(2)))}
            onZoomOut={() => setZoom((z) => Math.max(0.4, +(z - 0.1).toFixed(2)))}
            onZoomReset={() => setZoom(1.0)}
            pageCount={pages.length}
          />
        )}
      </div>

      {/* Add-Page-Dialog */}
      {addPageState && (
        <AddPageDialog
          parentId={addPageState.parent_id}
          parentName={addPageState.parent_id
            ? (pages.find((p) => p.id === addPageState.parent_id)?.page_name || '')
            : null}
          onClose={() => setAddPageState(null)}
          onSubmit={async (name, type) => {
            const created = await createPage(addPageState.parent_id, name, type, addPageState.position);
            if (created) setAddPageState(null);
          }}
        />
      )}

      {/* Add-Section-Dialog */}
      {addSectionState && (
        <AddSectionDialog
          existingSections={(pages.find((p) => p.id === addSectionState.page_id)?.sections) || []}
          onClose={() => setAddSectionState(null)}
          onPick={(sectionKey) => {
            addSectionToPage(addSectionState.page_id, sectionKey, addSectionState.position);
            setAddSectionState(null);
          }}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PageColumn — eine Page-Karte + ihre Kinder als Reihe darunter (mit Connectors)
// ─────────────────────────────────────────────────────────────────────────────

