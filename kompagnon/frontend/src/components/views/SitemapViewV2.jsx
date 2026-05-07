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
import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

// Spiegelung des Backend-SECTION_CATALOG (routers/sitemap.py).
const SECTION_CATALOG = {
  header_nav:          'Sticky-Header: Logo + Hauptnavigation + ggf. CTA-Button',
  hero_value_equation: 'Hero mit Hormozi-Outcome+Time+Effort-Versprechen (Startseite)',
  hero_service:        'Hero für Service-Detail-Page mit klarem Outcome',
  hero_minimal:        'Kompakter Hero — für Über uns / Kontakt / Rechtliches',
  problem:             'Pain-Point-Section — typische Schmerzen der Zielgruppe',
  offer_stack:         'Hormozi-Wertbox: EUR-Positionen + Gesamtwert + Anker',
  process_steps:       '4-6 nummerierte Schritte mit Zeitangabe',
  guarantee_block:     '5 AGB-konforme Garantien (Risk Reversal)',
  urgency_block:       'Echte Stichtage (BAFA/GEG/Slot-Cap)',
  trust_strip:         'Logo-Streifen (Innung, Hersteller, Zertifikate)',
  fallstudien_3:       '3 Fallstudien-Cards mit Zahlen',
  service_grid:        'Übersicht aller Services',
  team:                'Team-/Meister-Vorstellung mit Fotos',
  faq:                 'Allgemeine FAQ — 8-12 Fragen',
  faq_service:         'Service-spezifische FAQ',
  content_richtext:    'Reiner Fließtext-Block — für Info-/Rechtsseiten',
  cta_inline:          'Inline-CTA zwischen Sections',
  cta_final:           'Finale CTA + Sticky-Mobile-Bottom-Bar',
  contact_form:        'Kontakt-Formular mit Tel/Mail/WhatsApp',
  footer_legal:        'Footer mit Pflicht-Links',
};

// Lesbare Labels fuer die Section-Keys in der Page-Card.
const SECTION_LABEL = {
  header_nav:          'Header / Navigation',
  hero_value_equation: 'Hero (Value-Equation)',
  hero_service:        'Hero (Service)',
  hero_minimal:        'Hero (Minimal)',
  problem:             'Problem-Section',
  offer_stack:         'Offer-Stack',
  process_steps:       'Prozess-Schritte',
  guarantee_block:     'Garantien',
  urgency_block:       'Urgency / Stichtage',
  trust_strip:         'Trust-Strip',
  fallstudien_3:       'Fallstudien (3)',
  service_grid:        'Service-Grid',
  team:                'Team',
  faq:                 'FAQ',
  faq_service:         'FAQ (Service)',
  content_richtext:    'Fließtext-Block',
  cta_inline:          'CTA (inline)',
  cta_final:           'CTA (final)',
  contact_form:        'Kontakt-Formular',
  footer_legal:        'Footer',
};

const PAGE_TYPE_OPTIONS = [
  { value: 'startseite', label: 'Startseite' },
  { value: 'leistung',   label: 'Leistungsseite' },
  { value: 'info',       label: 'Info-Seite' },
  { value: 'vertrauen',  label: 'Vertrauensseite' },
  { value: 'conversion', label: 'Kontakt' },
  { value: 'rechtlich',  label: 'Rechtlich' },
  { value: 'sonstige',   label: 'Sonstige' },
  { value: 'ground',     label: 'Übersicht' },
];

const TYPE_META = {
  startseite: { label: 'Startseite',      icon: '🏠' },
  leistung:   { label: 'Leistungsseite',  icon: '🔧' },
  info:       { label: 'Info-Seite',      icon: 'ℹ️' },
  vertrauen:  { label: 'Vertrauensseite', icon: '⭐' },
  conversion: { label: 'Kontakt',         icon: '📞' },
  rechtlich:  { label: 'Rechtlich',       icon: '⚖️' },
  sonstige:   { label: 'Sonstige',        icon: '📄' },
  ground:     { label: 'Übersicht',       icon: '📋' },
};

const PAGE_W = 280;       // Pixel-Breite einer Page-Karte
const COL_GAP = 40;       // Abstand zwischen Geschwister-Spalten
const ROW_GAP = 56;       // Abstand zwischen Eltern und Kinder-Reihe (inkl. Connector)

// Phase C: Link-Extraktion aus Block-Slots
// ─────────────────────────────────────────────────────────────────────────────
// Heuristik: ein Slot ist ein Link wenn:
//   - sein Key 'url'/'link'/'href' enthaelt, ODER
//   - sein Wert mit http(s)://, /, oder # beginnt
// Externe Links: http(s):// (nicht auf eine eigene sitemap_page deutend)
// Interne Links: relativer Pfad oder URL deren letzter Path-Teil mit einer
//                Page in dieser Sitemap matcht (slugified page_name).

function slugify(s) {
  if (!s || typeof s !== 'string') return '';
  return s.toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function isUrlSlot(key, value) {
  if (!value || typeof value !== 'string') return false;
  const k = (key || '').toLowerCase();
  if (k.includes('url') || k.includes('link') || k.includes('href')) return true;
  return /^(https?:\/\/|\/|#)/.test(value.trim());
}

function isExternalUrl(value) {
  return /^https?:\/\//i.test(value || '');
}

// Versucht, einen Link-Wert auf eine Page in der Sitemap zu mappen.
// Strategien:
//   - relativer Pfad (/wallbox-installation) → Slug-Match
//   - http(s)://eigene-domain/path → Path-Match
//   - reines Page-Name-Fragment → Slug-Match
function matchInternalPage(value, pageSlugMap) {
  if (!value || typeof value !== 'string') return null;
  let v = value.trim();
  // http(s):// strippen, um den Path zu bekommen
  if (/^https?:\/\//i.test(v)) {
    try {
      const url = new URL(v);
      v = url.pathname + (url.hash || '');
    } catch (_) {
      return null;
    }
  }
  // Hash-/Anker-Links '#section' sind seitenintern → nicht auf andere Page mappen
  if (v.startsWith('#')) return null;
  // Slashes + trailing entfernen
  const cleaned = v.replace(/^\/+|\/+$/g, '').toLowerCase();
  if (!cleaned) return null;
  // Direkter Slug-Match
  if (pageSlugMap.has(cleaned)) return pageSlugMap.get(cleaned);
  // Erstes Segment als Slug versuchen (z.B. /wallbox-installation/foerderung)
  const firstSegment = cleaned.split('/')[0];
  if (firstSegment && pageSlugMap.has(firstSegment)) return pageSlugMap.get(firstSegment);
  return null;
}

// ─────────────────────────────────────────────────────────────────────────────

// Phase 2: Globale Sections — werden konventionell auf jeder Seite verwendet.
// In der Add-Sidebar oben hervorgehoben mit Instance-Count.
const GLOBAL_SECTION_KEYS = ['header_nav', 'footer_legal'];

// Kategorien fuer die Add-Sidebar — gruppiert nach semantischer Naehe.
const SIDEBAR_CATEGORIES = [
  { label: 'Hero',                items: ['hero_value_equation', 'hero_service', 'hero_minimal'] },
  { label: 'Problem & Offer',     items: ['problem', 'offer_stack'] },
  { label: 'Trust / Social Proof', items: ['guarantee_block', 'urgency_block', 'trust_strip', 'fallstudien_3'] },
  { label: 'Process',             items: ['process_steps'] },
  { label: 'Service & Team',      items: ['service_grid', 'team'] },
  { label: 'FAQ',                 items: ['faq', 'faq_service'] },
  { label: 'Content',             items: ['content_richtext'] },
  { label: 'CTA & Contact',       items: ['cta_inline', 'cta_final', 'contact_form'] },
];

// ─────────────────────────────────────────────────────────────────────────────

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
      background: '#f8fafc',
    }}>
      {/* Topbar */}
      <div style={{
        flexShrink: 0,
        padding: '14px 24px',
        background: '#fff',
        borderBottom: '1px solid #e2e8f0',
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
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
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
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
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
          {loading && <div style={{ color: '#64748b' }}>Sitemap wird geladen…</div>}
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

function PageColumn({
  page, tree,
  selectedPageId, onSelect,
  onAddSibling, onAddChild, onDelete, onDuplicate, onAddSection, onRemoveSection, onToggleGroup,
  isFirstSibling = false,
  dragState, setDragState, dropTarget, setDropTarget, moveSection, endDrag,
  inheritedSections = null,  // Phase 4: nicht-null wenn Eltern-Page eine Gruppe ist
  linksByPageId = null, pages = null,
  setCardRef = null,
}) {
  const children = tree.get(page.id) || [];
  const isActive = selectedPageId === page.id;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: COL_GAP / 2 }}>
        <PageCard
          page={page}
          isActive={isActive}
          onSelect={onSelect}
          onAddChild={onAddChild}
          onDelete={onDelete}
          onDuplicate={onDuplicate}
          onAddSection={onAddSection}
          onRemoveSection={onRemoveSection}
          onToggleGroup={onToggleGroup}
          inheritedSections={inheritedSections}
          dragState={dragState}
          setDragState={setDragState}
          dropTarget={dropTarget}
          setDropTarget={setDropTarget}
          moveSection={moveSection}
          endDrag={endDrag}
          links={linksByPageId?.get(page.id)}
          pages={pages}
          onSelectPage={onSelect}
          setCardRef={setCardRef}
        />
        {/* "+" zwischen Geschwistern (rechts von dieser Karte) */}
        <AddPagePlus
          onClick={() => onAddSibling((page.position ?? 0) + 1)}
        />
      </div>

      {/* Kinder-Row: gleiche Logik rekursiv */}
      {children.length > 0 && (
        <div style={{ marginTop: ROW_GAP, position: 'relative' }}>
          {/* Vertikaler Connector von Eltern-Bottom zu Kinder-Reihe */}
          <div style={{
            position: 'absolute',
            top: -ROW_GAP,
            left: '50%', transform: 'translateX(-50%)',
            width: 1, height: ROW_GAP / 2,
            background: '#cbd5e1',
          }} />
          {/* Horizontale Linie ueber alle Kinder */}
          {children.length > 1 && (
            <div style={{
              position: 'absolute',
              top: -ROW_GAP / 2,
              left: 0, right: 0,
              height: 1,
              background: '#cbd5e1',
            }} />
          )}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: COL_GAP / 2 }}>
            {children.map((c, idx) => (
              <ChildPageColumn
                key={c.id}
                page={c} tree={tree}
                selectedPageId={selectedPageId}
                onSelect={onSelect}
                onAddSibling={(afterPos) => onAddChild(page.id, afterPos)}
                onAddChild={onAddChild}
                onDelete={onDelete}
                onDuplicate={onDuplicate}
                onAddSection={onAddSection}
                onRemoveSection={onRemoveSection}
                onToggleGroup={onToggleGroup}
                isFirstSibling={idx === 0}
                dragState={dragState}
                setDragState={setDragState}
                dropTarget={dropTarget}
                setDropTarget={setDropTarget}
                moveSection={moveSection}
                endDrag={endDrag}
                inheritedSections={page.is_group ? (page.group_template_sections || []) : null}
                linksByPageId={linksByPageId}
                pages={pages}
                setCardRef={setCardRef}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Wrapper fuer rekursives Rendering — children verhalten sich gleich.
// Eigene Komponente damit die Connector-Linie pro Kind individuell ist.
function ChildPageColumn(props) {
  return (
    <div style={{ position: 'relative' }}>
      {/* Vertikale Linie ueber jedem Kind, verbindet zur horizontalen Eltern-Linie */}
      <div style={{
        position: 'absolute',
        top: -ROW_GAP / 2,
        left: '50%', transform: 'translateX(-50%)',
        width: 1, height: ROW_GAP / 2,
        background: '#cbd5e1',
      }} />
      <PageColumn {...props} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PageCard — Header + Section-Liste + Add-Section-Button
// ─────────────────────────────────────────────────────────────────────────────

function PageCard({
  page,
  isActive, onSelect,
  onAddChild, onDelete, onDuplicate, onAddSection, onRemoveSection, onToggleGroup,
  inheritedSections = null,
  dragState, setDragState, dropTarget, setDropTarget, moveSection, endDrag,
  links = null, pages = null, onSelectPage = null,
  setCardRef = null,
}) {
  const [linksOpen, setLinksOpen] = useState(false);
  const internalLinks = links?.internal || [];
  const externalLinks = links?.external || [];
  const hasLinks = internalLinks.length > 0 || externalLinks.length > 0;
  const meta = TYPE_META[page.page_type] || TYPE_META.info;
  // Phase 4: Section-Anzeige bestimmen.
  // - Page ist selbst Gruppe? → group_template_sections (editierbar als Template)
  // - Eltern ist Gruppe? → inheritedSections (read-only, vom Template uebernommen)
  // - Sonst: page.sections
  const isGroup = !!page.is_group;
  const isInherited = !isGroup && inheritedSections != null;
  const sections = isGroup
    ? (Array.isArray(page.group_template_sections) ? page.group_template_sections : [])
    : isInherited
    ? inheritedSections
    : (Array.isArray(page.sections) ? page.sections : []);
  const sectionsEditable = !isInherited; // Inherited = read-only
  const [menuOpen, setMenuOpen] = useState(false);
  const cardRef = useRef(null);

  // Phase C polish: Card-DOM-Node beim Parent registrieren fuer SVG-Edges
  useEffect(() => {
    if (!setCardRef) return;
    setCardRef(page.id, cardRef.current);
    return () => setCardRef(page.id, null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page.id]);

  // Outside click schliesst Menu
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e) => {
      if (!cardRef.current?.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  const cardClick = (e) => {
    if (e.target.closest('[data-noselect]')) return;
    onSelect?.(page.id);
  };

  return (
    <div
      ref={cardRef}
      onClick={cardClick}
      style={{
        position: 'relative',
        width: PAGE_W, flexShrink: 0,
        background: '#fff',
        border: isActive
          ? `2px solid ${KC_MID}`
          : isGroup
          ? `1px solid ${KC_MID}`
          : '1px solid #e2e8f0',
        borderRadius: 10,
        boxShadow: isActive
          ? `0 4px 16px ${KC_MID}33`
          : '0 1px 3px rgba(0,0,0,0.04)',
        cursor: 'pointer',
        overflow: 'visible',
      }}
    >
      {/* Page-Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 12px',
        background: isGroup ? '#ecfeff' : '#f8fafc',
        borderBottom: '1px solid #e2e8f0',
        borderTopLeftRadius: 10, borderTopRightRadius: 10,
      }}>
        <span style={{ fontSize: 14, flexShrink: 0 }}>
          {isGroup ? '📂' : meta.icon}
        </span>
        <div style={{
          flex: 1, minWidth: 0,
          fontSize: 12, fontWeight: 700, color: KC_DARK,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {page.page_name}
        </div>
        {isGroup && (
          <span style={{
            fontSize: 9, fontWeight: 800, color: '#fff', background: KC_MID,
            padding: '2px 6px', borderRadius: 4,
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}>
            Gruppe
          </span>
        )}
        {page.ist_pflichtseite && (
          <span title="Pflichtseite" style={{ fontSize: 11 }}>🔒</span>
        )}
        <button
          type="button" data-noselect
          onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v); }}
          aria-label="Menü"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#64748b', fontSize: 16, lineHeight: 1, padding: '0 4px',
            fontWeight: 700,
          }}
        >
          ⋯
        </button>
      </div>

      {/* Section-Liste */}
      <div style={{ padding: '8px 12px 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {isInherited && (
          <div style={{
            marginBottom: 4, padding: '4px 8px',
            fontSize: 10, color: '#0e7490',
            background: '#ecfeff', border: '1px solid #a5f3fc',
            borderRadius: 4,
          }}>
            🔗 Sections aus übergeordneter Gruppe — Änderungen oben in der Gruppe.
          </div>
        )}
        {isGroup && (
          <div style={{
            marginBottom: 4, padding: '4px 8px',
            fontSize: 10, color: '#0e7490',
            background: '#ecfeff', border: '1px solid #a5f3fc',
            borderRadius: 4,
          }}>
            📂 Section-Template — wird automatisch von allen Kind-Pages übernommen.
          </div>
        )}
        {sections.length === 0 ? (
          <div data-noselect style={{
            padding: '20px 8px', textAlign: 'center',
            color: '#94a3b8', fontSize: 11, fontStyle: 'italic',
          }}>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onAddSection(page.id, 0); }}
              style={{
                width: '100%', padding: '10px 12px',
                background: '#f8fafc', border: '1px dashed #cbd5e1',
                borderRadius: 6, fontSize: 12, fontWeight: 700,
                color: KC_MID, cursor: 'pointer', fontFamily: 'inherit',
                marginBottom: 6,
              }}
            >
              + Section
            </button>
            <div style={{ fontSize: 10, color: '#cbd5e1' }}>oder</div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                // Phase B: KI-Generate ist im Wireframe-View — hier nur Hint
                toast('Tipp: Wechsel in den Wireframe-View für KI-Content-Generierung.');
              }}
              style={{
                marginTop: 6, padding: '8px 12px',
                background: 'transparent', border: 'none',
                fontSize: 11, color: '#7c3aed', fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              ✨ Generate content
            </button>
          </div>
        ) : isInherited ? (
          // Phase 4: read-only Anzeige der geerbten Sections (vom Eltern-Group).
          sections.map((key, idx) => (
            <InheritedSectionRow key={`${key}-${idx}`} sectionKey={key} idx={idx} />
          ))
        ) : (
          <>
            {/* DropZone vor erster Section */}
            <DropZone
              pageId={page.id} position={0}
              dragState={dragState} dropTarget={dropTarget}
              setDropTarget={setDropTarget}
              onDrop={moveSection} endDrag={endDrag}
            />
            {sections.map((key, idx) => (
              <Fragment key={`${key}-${idx}`}>
                <SectionRow
                  sectionKey={key} idx={idx} pageId={page.id}
                  onRemove={() => onRemoveSection(page.id, idx)}
                  onAddBelow={() => onAddSection(page.id, idx + 1)}
                  dragState={dragState} setDragState={setDragState}
                  endDrag={endDrag}
                />
                <DropZone
                  pageId={page.id} position={idx + 1}
                  dragState={dragState} dropTarget={dropTarget}
                  setDropTarget={setDropTarget}
                  onDrop={moveSection} endDrag={endDrag}
                />
              </Fragment>
            ))}
            {/* "+" unter der letzten Section */}
            <button
              type="button" data-noselect
              onClick={(e) => { e.stopPropagation(); onAddSection(page.id, sections.length); }}
              style={{
                marginTop: 4, padding: '6px 10px',
                background: 'transparent', border: '1px dashed #cbd5e1',
                borderRadius: 6, fontSize: 11, fontWeight: 600,
                color: KC_MID, cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              + Section hinzufügen
            </button>
          </>
        )}
      </div>

      {/* Phase C: Link-Footer — zeigt Anzahl interner/externer Links der Page */}
      {hasLinks && (
        <div data-noselect style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 12px',
          borderTop: '1px solid #e2e8f0',
          background: linksOpen ? '#eff6ff' : '#f8fafc',
          fontSize: 10,
          cursor: 'pointer',
        }} onClick={(e) => { e.stopPropagation(); setLinksOpen((v) => !v); }}>
          {internalLinks.length > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 3,
              padding: '2px 6px', borderRadius: 4,
              background: '#dbeafe', color: '#1e40af',
              fontWeight: 700,
            }}>
              🔗 {internalLinks.length} intern
            </span>
          )}
          {externalLinks.length > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 3,
              padding: '2px 6px', borderRadius: 4,
              background: '#f1f5f9', color: '#64748b',
              fontWeight: 700,
            }}>
              ↗ {externalLinks.length} extern
            </span>
          )}
          <span style={{ flex: 1 }} />
          <span style={{ color: '#94a3b8', fontSize: 9 }}>
            {linksOpen ? '▲' : '▼'}
          </span>
        </div>
      )}

      {/* Phase C: Link-Detail-Popover — eingeklappte Liste der Ziele */}
      {hasLinks && linksOpen && (
        <div data-noselect onClick={(e) => e.stopPropagation()} style={{
          padding: '8px 10px',
          background: '#f8fafc',
          borderTop: '1px solid #e2e8f0',
          fontSize: 10, color: '#475569',
          maxHeight: 200, overflowY: 'auto',
        }}>
          {internalLinks.length > 0 && (
            <>
              <div style={{
                fontSize: 9, fontWeight: 700, color: '#1e40af',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                marginBottom: 4,
              }}>
                Intern ({internalLinks.length})
              </div>
              {internalLinks.map((l, i) => {
                const target = pages?.find((p) => p.id === l.toPageId);
                return (
                  <button
                    key={`int-${i}`} type="button"
                    onClick={() => { setLinksOpen(false); onSelectPage?.(l.toPageId); }}
                    title={`Slot „${l.slot}" → ${l.value}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4, width: '100%',
                      padding: '4px 6px', marginBottom: 2,
                      background: '#fff', border: '1px solid #dbeafe', borderRadius: 4,
                      fontSize: 10, fontFamily: 'inherit', color: '#1e40af',
                      cursor: 'pointer', textAlign: 'left',
                    }}
                  >
                    <span style={{ flex: 1, minWidth: 0,
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 600,
                    }}>
                      → {target?.page_name || `Page #${l.toPageId}`}
                    </span>
                    <code style={{ fontSize: 9, color: '#64748b', fontFamily: 'ui-monospace, monospace' }}>
                      {l.slot}
                    </code>
                  </button>
                );
              })}
            </>
          )}
          {externalLinks.length > 0 && (
            <>
              <div style={{
                fontSize: 9, fontWeight: 700, color: '#475569',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                marginTop: internalLinks.length > 0 ? 6 : 0, marginBottom: 4,
              }}>
                Extern ({externalLinks.length})
              </div>
              {externalLinks.map((l, i) => (
                <a key={`ext-${i}`}
                  href={l.url} target="_blank" rel="noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  title={`Slot „${l.slot}"${l.unresolved ? ' — interner Pfad ohne Ziel' : ''}`}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    padding: '4px 6px', marginBottom: 2,
                    background: '#fff',
                    border: `1px solid ${l.unresolved ? '#fca5a5' : '#e2e8f0'}`,
                    borderRadius: 4,
                    fontSize: 10, color: l.unresolved ? '#991B1B' : '#475569',
                    textDecoration: 'none',
                    overflow: 'hidden',
                  }}
                >
                  <span style={{ flex: 1, minWidth: 0,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {l.unresolved ? '⚠ ' : '↗ '}
                    {l.url}
                  </span>
                  <code style={{ fontSize: 9, color: '#94a3b8', fontFamily: 'ui-monospace, monospace' }}>
                    {l.slot}
                  </code>
                </a>
              ))}
            </>
          )}
        </div>
      )}

      {/* Context-Menu (Dropdown) */}
      {menuOpen && (
        <div
          data-noselect
          style={{
            position: 'absolute', top: 38, right: 8, zIndex: 50,
            background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
            boxShadow: '0 6px 20px rgba(0,0,0,0.10)',
            minWidth: 180, padding: 4,
            display: 'flex', flexDirection: 'column',
          }}
        >
          <MenuItem onClick={() => { setMenuOpen(false); onAddChild(page.id); }}>+ Sub-Seite</MenuItem>
          <MenuItem
            onClick={() => { setMenuOpen(false); onAddSection(page.id, sections.length); }}
            disabled={isInherited}
          >
            + Section
          </MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onDuplicate(page.id); }}>📋 Duplizieren</MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onSelect(page.id); }}>✏️ Bearbeiten…</MenuItem>
          <div style={{ height: 1, background: '#e2e8f0', margin: '4px 2px' }} />
          <MenuItem
            onClick={() => { setMenuOpen(false); onToggleGroup(page.id); }}
            disabled={page.ist_pflichtseite}
          >
            {isGroup ? '↩ Zurück zur Page' : '📂 Als Gruppe markieren'}
          </MenuItem>
          <div style={{ height: 1, background: '#e2e8f0', margin: '4px 2px' }} />
          <MenuItem
            danger
            disabled={page.ist_pflichtseite}
            onClick={() => { setMenuOpen(false); onDelete(page.id); }}
          >
            🗑 Löschen
          </MenuItem>
        </div>
      )}
    </div>
  );
}

function MenuItem({ children, onClick, danger, disabled }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled}
      style={{
        background: 'transparent', border: 'none',
        padding: '6px 10px', textAlign: 'left',
        fontSize: 12, fontWeight: 600,
        color: disabled ? '#cbd5e1' : danger ? '#dc2626' : '#475569',
        cursor: disabled ? 'not-allowed' : 'pointer',
        borderRadius: 4, fontFamily: 'inherit',
      }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.background = danger ? '#FEF2F2' : '#f1f5f9';
      }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      {children}
    </button>
  );
}

// Eine Section-Reihe in der Page-Karte. Phase 3: native HTML5 drag — die
// Section selbst ist die Drag-Quelle. Drop-Targets sind die DropZones zwischen
// den Sections.
function SectionRow({
  sectionKey, idx, pageId, onRemove, onAddBelow,
  dragState, setDragState, endDrag,
}) {
  const label = SECTION_LABEL[sectionKey] || sectionKey;
  const desc = SECTION_CATALOG[sectionKey] || '';
  const [hover, setHover] = useState(false);

  const isBeingDragged =
    dragState && dragState.fromPageId === pageId && dragState.fromIdx === idx;

  return (
    <div
      data-noselect
      draggable
      onDragStart={(e) => {
        e.stopPropagation();
        setDragState({ fromPageId: pageId, fromIdx: idx, sectionKey });
        // Damit Firefox den Drag akzeptiert — Payload wird per State gefuehrt
        try { e.dataTransfer.setData('text/plain', sectionKey); } catch (_) {}
        e.dataTransfer.effectAllowed = 'move';
      }}
      onDragEnd={(e) => { e.stopPropagation(); endDrag(); }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative',
        padding: '8px 10px',
        background: hover ? '#f8fafc' : '#fff',
        border: '1px solid #e2e8f0', borderRadius: 6,
        fontSize: 11,
        cursor: 'grab',
        opacity: isBeingDragged ? 0.4 : 1,
        transition: 'opacity 0.1s',
      }}
    >
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2,
      }}>
        <span aria-hidden style={{ color: '#cbd5e1', fontSize: 12, lineHeight: 1, userSelect: 'none' }}>⠿</span>
        <span style={{ color: '#cbd5e1', fontVariantNumeric: 'tabular-nums', minWidth: 14, fontSize: 10 }}>
          {idx + 1}
        </span>
        <span style={{ fontWeight: 700, color: KC_DARK, flex: 1, minWidth: 0,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {label}
        </span>
        {hover && (
          <button
            type="button" onClick={(e) => { e.stopPropagation(); onRemove(); }}
            aria-label="Section entfernen"
            style={{
              background: 'none', border: 'none',
              fontSize: 12, color: '#dc2626', cursor: 'pointer', padding: 0,
            }}
          >
            ×
          </button>
        )}
      </div>
      <div style={{
        fontSize: 10, color: '#64748b',
        lineHeight: 1.35,
        display: '-webkit-box',
        WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {desc}
      </div>
      {hover && !dragState && (
        <button
          type="button" onClick={(e) => { e.stopPropagation(); onAddBelow(); }}
          aria-label="Section darunter einfügen"
          style={{
            position: 'absolute',
            bottom: -10, left: '50%', transform: 'translateX(-50%)',
            width: 18, height: 18, borderRadius: '50%',
            background: '#fff', border: `1px solid ${KC_MID}`,
            color: KC_MID, fontSize: 12, lineHeight: 1,
            cursor: 'pointer', zIndex: 5,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 0, fontFamily: 'inherit', fontWeight: 700,
          }}
        >
          +
        </button>
      )}
    </div>
  );
}

// Phase 4: Read-only-Variante einer Section-Zeile, fuer Kinder einer Gruppe.
// Keine Drag-Handles, keine Remove/Add-Buttons — Aenderungen muessen am
// Eltern-Group gemacht werden.
function InheritedSectionRow({ sectionKey, idx }) {
  const label = SECTION_LABEL[sectionKey] || sectionKey;
  const desc = SECTION_CATALOG[sectionKey] || '';
  return (
    <div data-noselect style={{
      padding: '8px 10px',
      background: '#f8fafc',
      border: '1px dashed #cbd5e1', borderRadius: 6,
      fontSize: 11,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
        <span style={{ color: '#cbd5e1', fontVariantNumeric: 'tabular-nums', minWidth: 14, fontSize: 10 }}>
          {idx + 1}
        </span>
        <span style={{ fontWeight: 700, color: '#475569', flex: 1, minWidth: 0,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {label}
        </span>
      </div>
      <div style={{
        fontSize: 10, color: '#64748b',
        lineHeight: 1.35,
        display: '-webkit-box',
        WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {desc}
      </div>
    </div>
  );
}

// Phase 3: DropZone — duenner Spacer zwischen / nach Sections, der bei aktivem
// Drag als Drop-Target fungiert. Highlightet sich wenn der gezogene Eintrag
// drueber schwebt.
function DropZone({ pageId, position, dragState, dropTarget, setDropTarget, onDrop, endDrag }) {
  const isActive = !!dragState; // nur sichtbar wenn etwas gezogen wird
  const isHighlighted =
    dropTarget && dropTarget.pageId === pageId && dropTarget.position === position;

  // Self-drop nicht erlauben — ein Section kann nicht direkt vor oder hinter
  // sich selbst gedroppt werden (no-op Move).
  const isSelfPosition =
    dragState
    && dragState.fromPageId === pageId
    && (dragState.fromIdx === position || dragState.fromIdx + 1 === position);

  return (
    <div
      data-noselect
      onDragOver={(e) => {
        if (!isActive || isSelfPosition) return;
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'move';
        if (!isHighlighted) setDropTarget({ pageId, position });
      }}
      onDragLeave={(e) => {
        // Leave-Events feuern auch fuer Kinder; nur reagieren wenn wir wirklich
        // den DropZone verlassen.
        if (e.currentTarget.contains(e.relatedTarget)) return;
        if (isHighlighted) setDropTarget(null);
      }}
      onDrop={(e) => {
        if (!isActive || isSelfPosition) return;
        e.preventDefault();
        e.stopPropagation();
        onDrop({
          fromPageId: dragState.fromPageId,
          fromIdx:    dragState.fromIdx,
          toPageId:   pageId,
          toIdx:      position,
          sectionKey: dragState.sectionKey,
        });
        endDrag();
      }}
      style={{
        height: isActive ? (isHighlighted ? 14 : 8) : 2,
        margin: isActive ? '2px 0' : 0,
        borderRadius: 3,
        background: isHighlighted ? KC_MID : 'transparent',
        transition: 'height 0.1s, background 0.1s',
      }}
    />
  );
}

// "+"-Button zwischen / nach Pages
function AddPagePlus({ onClick, large = false }) {
  const size = large ? 36 : 28;
  return (
    <button
      type="button" onClick={onClick}
      aria-label="Seite hinzufügen"
      style={{
        flexShrink: 0,
        marginTop: 18,
        width: size, height: size, borderRadius: '50%',
        background: '#fff', border: `1.5px dashed ${KC_MID}`,
        color: KC_MID, fontSize: large ? 18 : 16, lineHeight: 1, fontWeight: 700,
        cursor: 'pointer', fontFamily: 'inherit',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 0,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = KC_MID;
        e.currentTarget.style.color = '#fff';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = '#fff';
        e.currentTarget.style.color = KC_MID;
      }}
    >
      +
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

function LinkEdgeOverlay({ tick, cardRefs, canvasInnerRef, linksByPageId }) {
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

function AddSidebar({ pages, activePageId, onAddToActivePage, setDragState, endDrag }) {
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
        background: '#fff', borderRight: '1px solid #e2e8f0',
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
      background: '#fff', borderRight: '1px solid #e2e8f0',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      fontFamily: 'inherit',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 14px', borderBottom: '1px solid #e2e8f0',
      }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: KC_DARK, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Add
        </div>
        <button type="button" onClick={() => setCollapsed(true)}
          aria-label="Sidebar einklappen" title="Sidebar einklappen"
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', fontSize: 14, padding: 0 }}>
          ×
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: 10, borderBottom: '1px solid #e2e8f0' }}>
        <input
          type="search" placeholder="Suchen…"
          value={search} onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '7px 10px',
            border: '1px solid #e2e8f0', borderRadius: 6,
            fontSize: 12, fontFamily: 'inherit', outline: 'none',
          }}
        />
      </div>

      {/* Scroll-Bereich */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
        {!activePageId && (
          <div style={{
            margin: '0 0 10px',
            padding: '8px 10px', fontSize: 11, color: '#92400e',
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
            fontSize: 10, fontWeight: 700, color: '#64748b',
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
                onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                <span style={{ color: '#94a3b8', fontSize: 10, flexShrink: 0 }}>
                  {isOpen ? '▼' : '▶'}
                </span>
                <span style={{ fontSize: 12, fontWeight: 700, color: KC_DARK }}>
                  {cat.label}
                </span>
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: 10, color: '#94a3b8' }}>{items.length}</span>
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

function SidebarSectionItem({ sectionKey, count, global = false, onPick, setDragState, endDrag }) {
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
        fontSize: 11,
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
        background: global ? '#10b981' : '#cbd5e1', flexShrink: 0,
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
          background: '#f1f5f9', color: '#64748b',
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

function EmptyState({ onAddPage, onRegenerateSitemap }) {
  return (
    <div style={{
      maxWidth: 480, margin: '60px auto',
      border: '2px dashed #cbd5e1', borderRadius: 16, padding: 40,
      textAlign: 'center', color: '#64748b', background: '#fff',
    }}>
      <div style={{ fontSize: 36, marginBottom: 8 }}>🗺</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: KC_DARK, marginBottom: 8 }}>
        Noch keine Sitemap-Seiten
      </div>
      <div style={{ fontSize: 13, marginBottom: 20 }}>
        Lege manuell Seiten an oder lass die KI eine Struktur vorschlagen.
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
        <button type="button" onClick={onAddPage} style={btnTeal}>
          + Erste Seite
        </button>
        <button type="button" onClick={() => onRegenerateSitemap?.(0)} style={btnYellow}>
          ⚡ KI-Vorschlag
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Side-Panel: Page-Details (Name / Type / Status / KI-Prompt)
// ─────────────────────────────────────────────────────────────────────────────

function PageDetailPanel({ page, onClose, onSave, onDelete }) {
  const [form, setForm] = useState(() => ({
    page_name: page?.page_name || '',
    page_type: page?.page_type || 'info',
    status:    page?.status    || 'geplant',
    ai_prompt: page?.ai_prompt || '',
  }));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      page_name: page?.page_name || '',
      page_type: page?.page_type || 'info',
      status:    page?.status    || 'geplant',
      ai_prompt: page?.ai_prompt || '',
    });
  }, [page?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!page) return null;
  const isPflicht = !!page.ist_pflichtseite;

  const handleSave = async () => {
    setSaving(true);
    await onSave(form);
    setSaving(false);
  };

  return (
    <aside style={{
      width: 340, flexShrink: 0,
      background: '#fff',
      borderLeft: '1px solid #e2e8f0',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid #e2e8f0',
        background: '#f8fafc',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK }}>
          Seiten-Details
        </div>
        <button type="button" onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: '#64748b', padding: 0 }}>×</button>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {isPflicht && (
          <div style={{ fontSize: 11, color: '#92400E', background: '#FEF3C7', padding: '6px 8px', borderRadius: 6 }}>
            🔒 Pflichtseite — Name / Type sind gesperrt.
          </div>
        )}
        <div>
          <label style={lblStyle}>Page-Name</label>
          <input type="text" value={form.page_name} disabled={isPflicht}
            onChange={(e) => setForm((f) => ({ ...f, page_name: e.target.value }))}
            style={inpStyle(isPflicht)} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={lblStyle}>Type</label>
            <select value={form.page_type} disabled={isPflicht}
              onChange={(e) => setForm((f) => ({ ...f, page_type: e.target.value }))}
              style={{ ...inpStyle(isPflicht), cursor: isPflicht ? 'not-allowed' : 'pointer' }}>
              {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label style={lblStyle}>Status</label>
            <select value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              style={{ ...inpStyle(false), cursor: 'pointer' }}>
              <option value="geplant">Geplant</option>
              <option value="in_bearbeitung">In Bearbeitung</option>
              <option value="freigegeben">Freigegeben</option>
              <option value="live">Live</option>
            </select>
          </div>
        </div>
        <div>
          <label style={lblStyle}>KI-Anweisung (optional)</label>
          <textarea value={form.ai_prompt}
            onChange={(e) => setForm((f) => ({ ...f, ai_prompt: e.target.value }))}
            placeholder="Goal / Per-Page-Kontext für KI-Generator"
            rows={4}
            style={{ ...inpStyle(false), resize: 'vertical', fontFamily: 'inherit', minHeight: 70 }} />
        </div>
      </div>
      <div style={{
        padding: '10px 14px', borderTop: '1px solid #e2e8f0',
        background: '#f8fafc',
        display: 'flex', justifyContent: 'space-between', gap: 8,
      }}>
        <button type="button" onClick={onDelete}
          disabled={isPflicht}
          style={{
            padding: '8px 12px',
            background: '#fff', border: `1px solid ${isPflicht ? '#cbd5e1' : '#fca5a5'}`,
            color: isPflicht ? '#cbd5e1' : '#dc2626',
            borderRadius: 6, fontSize: 12,
            cursor: isPflicht ? 'not-allowed' : 'pointer',
          }}>
          🗑 Löschen
        </button>
        <div style={{ display: 'flex', gap: 6 }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 12px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 12, color: '#64748b', cursor: 'pointer' }}>
            Abbrechen
          </button>
          <button type="button" onClick={handleSave} disabled={saving}
            style={{ padding: '8px 14px', background: saving ? '#94a3b8' : KC_DARK, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: saving ? 'wait' : 'pointer' }}>
            {saving ? 'Speichert…' : '✓ Speichern'}
          </button>
        </div>
      </div>
    </aside>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add-Page-Dialog (Modal)
// ─────────────────────────────────────────────────────────────────────────────

function AddPageDialog({ parentId, parentName, onClose, onSubmit }) {
  const [name, setName] = useState('');
  const [pageType, setPageType] = useState('info');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    await onSubmit(name, pageType);
    setBusy(false);
  };

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <form onSubmit={handleSubmit} style={{
        background: '#fff', borderRadius: 12, padding: 20,
        width: '100%', maxWidth: 420, boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <h3 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 700, color: KC_DARK }}>
          Neue Seite anlegen
        </h3>
        <p style={{ margin: '0 0 14px', fontSize: 11, color: '#64748b' }}>
          {parentId
            ? `Wird als Sub-Seite von „${parentName}" angelegt.`
            : 'Wird als Top-Level-Seite angelegt.'}
        </p>
        <div style={{ marginBottom: 10 }}>
          <label style={lblStyle}>Seitenname *</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="z.B. Wallbox-Installation"
            style={inpStyle(false)} autoFocus />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={lblStyle}>Page-Type</label>
          <select value={pageType} onChange={(e) => setPageType(e.target.value)}
            style={{ ...inpStyle(false), cursor: 'pointer' }}>
            {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, cursor: 'pointer', color: '#64748b' }}>
            Abbrechen
          </button>
          <button type="submit" disabled={!name.trim() || busy}
            style={{ padding: '8px 18px', background: !name.trim() || busy ? '#94a3b8' : KC_MID, color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: !name.trim() || busy ? 'not-allowed' : 'pointer' }}>
            {busy ? 'Anlegen…' : '+ Anlegen'}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add-Section-Dialog (Modal mit Section-Catalog)
// ─────────────────────────────────────────────────────────────────────────────

function AddSectionDialog({ existingSections, onClose, onPick }) {
  const [search, setSearch] = useState('');
  const all = Object.keys(SECTION_CATALOG);
  const used = new Set(existingSections);
  const filtered = all.filter((key) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return key.toLowerCase().includes(q) || SECTION_CATALOG[key].toLowerCase().includes(q);
  });

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 12,
        width: '100%', maxWidth: 520, maxHeight: 'calc(100vh - 32px)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: KC_DARK }}>
            Section auswählen
          </h3>
          <button type="button" onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: '#64748b' }}>×</button>
        </div>
        <div style={{ padding: '12px 18px', borderBottom: '1px solid #e2e8f0' }}>
          <input type="search" placeholder="Suchen…"
            value={search} onChange={(e) => setSearch(e.target.value)}
            style={inpStyle(false)} autoFocus />
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
          {filtered.length === 0 ? (
            <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 12, fontStyle: 'italic' }}>
              Kein Treffer für „{search}".
            </div>
          ) : (
            filtered.map((key) => {
              const isUsed = used.has(key);
              return (
                <button
                  key={key} type="button"
                  onClick={() => onPick(key)}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2,
                    width: '100%', padding: '8px 10px', marginBottom: 4,
                    background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6,
                    cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#eff6ff'; e.currentTarget.style.borderColor = KC_MID; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.borderColor = '#e2e8f0'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                    <code style={{ color: KC_MID, fontWeight: 700, fontSize: 11 }}>{key}</code>
                    <span style={{ flex: 1 }} />
                    {isUsed && (
                      <span style={{ fontSize: 9, color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>
                        bereits verwendet
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.4 }}>
                    {SECTION_CATALOG[key]}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared styles
// ─────────────────────────────────────────────────────────────────────────────

const lblStyle = {
  display: 'block', fontSize: 10, fontWeight: 700,
  color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em',
  marginBottom: 4,
};
const inpStyle = (disabled) => ({
  width: '100%', boxSizing: 'border-box', padding: '7px 10px',
  border: '1px solid #e2e8f0', borderRadius: 6,
  background: disabled ? '#f8fafc' : '#fff',
  color: disabled ? '#94a3b8' : '#1A2C32',
  fontSize: 12, fontFamily: 'inherit', outline: 'none',
});

const btnPrimary = {
  background: KC_YELLOW, color: '#000',
  border: 'none', borderRadius: 8,
  padding: '9px 16px', fontSize: 12, fontWeight: 800,
  cursor: 'pointer',
  textTransform: 'uppercase', letterSpacing: '0.04em',
  fontFamily: 'inherit',
};
const btnTeal = {
  background: KC_MID, color: '#fff',
  border: 'none', borderRadius: 8,
  padding: '9px 16px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
const btnYellow = {
  background: KC_YELLOW, color: '#000',
  border: 'none', borderRadius: 8,
  padding: '9px 16px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
const btnSecondary = {
  background: 'transparent', color: KC_DARK,
  border: `1.5px solid ${KC_DARK}`, borderRadius: 8,
  padding: '8px 14px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
