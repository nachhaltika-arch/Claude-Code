/**
 * SitemapView — Visueller Sitemap-Tree (Relume-Style) auf Reactflow-Basis.
 *
 * Phase 2 der Crawl-Import-Feature: Read-only Tree-Visualisierung der Pages.
 * Drag&Drop / Reorder kommt in Phase 4.
 *
 * Props:
 *   projectId             — Project.id
 *   leadId                — für /api/sitemap/{leadId}
 *   wireframeData         — aktueller Wireframe ({pages:[...]})
 *   onGenerateWireframe   — Callback: KI-Wireframe-Job
 *   onNavigateToWireframe — Callback: View-Switcher zu Wireframe
 *   onRegenerateSitemap   — Callback: KI-Sitemap-Vorschlag (existing)
 *
 * Datenquellen:
 *   GET  /api/sitemap/{leadId}                  — alle Pages
 *   POST /api/sitemap/{leadId}/import-existing  — Bestand crawlen (Phase 1)
 */
import { useEffect, useMemo, useState, useCallback } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  Panel,
} from '@xyflow/react';
import dagre from 'dagre';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

// Spiegelt SitemapPlaner-Konventionen — gleiche Farben/Icons
const TYPE_META = {
  startseite: { label: 'Startseite',      color: '#008EAA', icon: '🏠' },
  leistung:   { label: 'Leistungsseite',  color: '#2563EB', icon: '🔧' },
  info:       { label: 'Info-Seite',      color: '#059669', icon: 'ℹ️' },
  vertrauen:  { label: 'Vertrauensseite', color: '#D97706', icon: '⭐' },
  conversion: { label: 'Kontakt',         color: '#DC2626', icon: '📞' },
  rechtlich:  { label: 'Rechtlich',       color: '#6B7280', icon: '⚖️' },
  sonstige:   { label: 'Sonstige',        color: '#8B5CF6', icon: '📄' },
  ground:     { label: 'Übersicht',       color: '#0EA5E9', icon: '📋' },
};

// source → optionales Badge auf der Karte
const SOURCE_BADGE = {
  crawled:      { label: 'Bestand', bg: '#FEF3C7', color: '#92400E' },
  ki_generated: { label: 'KI',      bg: '#DCFCE7', color: '#166534' },
  manual:       { label: null,      bg: null,      color: null },
};

// Spiegelung des Backend-SECTION_CATALOG (routers/sitemap.py:81). Wenn das
// Backend hier neue Section-Keys einführt, muss das hier nachgezogen werden —
// ist aber bewusst kein eigener Endpoint, weil die Liste statisch ist.
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

const STATUS_OPTIONS = [
  { value: 'geplant',        label: 'Geplant' },
  { value: 'in_bearbeitung', label: 'In Bearbeitung' },
  { value: 'freigegeben',    label: 'Freigegeben' },
  { value: 'live',           label: 'Live' },
];

// Color-Tag-Presets (R1 Relume-Parität). Empty string = kein Tag.
const COLOR_TAG_PRESETS = [
  { value: '',        label: 'Kein Tag' },
  { value: '#FAE600', label: 'Gelb' },
  { value: '#008EAA', label: 'Teal' },
  { value: '#004F59', label: 'Dunkel-Teal' },
  { value: '#DC2626', label: 'Rot' },
  { value: '#059669', label: 'Grün' },
  { value: '#7C3AED', label: 'Violett' },
];

const PAGE_COUNT_OPTIONS = [
  { value: 0,  label: 'Auto (KI entscheidet)' },
  { value: 4,  label: '4 Seiten' },
  { value: 5,  label: '5 Seiten' },
  { value: 6,  label: '6 Seiten' },
  { value: 7,  label: '7 Seiten' },
  { value: 8,  label: '8 Seiten' },
  { value: 10, label: '10 Seiten' },
  { value: 12, label: '12 Seiten' },
];

const NODE_W = 240;
// Höhe variabel je nach Section-Anzahl. Min 110, +14 px pro sichtbarer Section
// (max 5 sichtbar, Rest als „+N more"-Zeile). Wird beim Layout pro Node
// berechnet, damit dagre die Karten kollisionsfrei platziert.
const NODE_H_BASE = 110;
const SECTION_LINE_H = 14;
const MAX_VISIBLE_SECTIONS = 5;

function nodeHeightForSections(sectionCount) {
  if (sectionCount <= 0) return NODE_H_BASE;
  const visible = Math.min(sectionCount, MAX_VISIBLE_SECTIONS);
  const overflow = sectionCount > MAX_VISIBLE_SECTIONS ? 1 : 0;
  return NODE_H_BASE + (visible + overflow) * SECTION_LINE_H + 8;
}

// ── Custom Node ──────────────────────────────────────────────────────────────

function PageNode({ data }) {
  const { page, blockCount } = data;
  const meta = TYPE_META[page.page_type] || TYPE_META.info;
  const sourceBadge = SOURCE_BADGE[page.source] || SOURCE_BADGE.manual;
  const hasColorTag = !!page.color_tag;

  return (
    <div style={{
      width: NODE_W,
      background: '#fff',
      border: `2px solid ${meta.color}`,
      borderLeft: hasColorTag ? `6px solid ${page.color_tag}` : `2px solid ${meta.color}`,
      borderRadius: 12,
      padding: '10px 12px',
      boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      <Handle type="target" position={Position.Top}
        style={{ background: meta.color, width: 8, height: 8, border: 'none' }}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 18, flexShrink: 0 }}>{meta.icon}</span>
        <div style={{
          fontWeight: 700, fontSize: 13, color: KC_DARK,
          flex: 1, minWidth: 0,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {page.page_name}
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
        <span style={{
          fontSize: 9, fontWeight: 700,
          padding: '2px 6px', borderRadius: 4,
          background: meta.color + '15', color: meta.color,
          textTransform: 'uppercase', letterSpacing: '0.04em',
        }}>
          {meta.label}
        </span>
        {sourceBadge.label && (
          <span style={{
            fontSize: 9, fontWeight: 700,
            padding: '2px 6px', borderRadius: 4,
            background: sourceBadge.bg, color: sourceBadge.color,
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            {sourceBadge.label}
          </span>
        )}
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontSize: 11, color: '#64748b',
      }}>
        <span>{blockCount} Block{blockCount === 1 ? '' : 's'}</span>
        {page.original_url ? (
          <a
            href={page.original_url} target="_blank" rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{ color: KC_MID, textDecoration: 'none', fontSize: 11, fontWeight: 600 }}
          >
            ↗ Original
          </a>
        ) : null}
      </div>

      {/* Section-Liste — zeigt die Hormozi-Sections der Page direkt im Tree */}
      {Array.isArray(page.sections) && page.sections.length > 0 && (
        <div style={{
          marginTop: 8, paddingTop: 8,
          borderTop: '1px dashed #e2e8f0',
          display: 'flex', flexDirection: 'column', gap: 2,
        }}>
          {page.sections.slice(0, MAX_VISIBLE_SECTIONS).map((key, idx) => (
            <div key={`${key}-${idx}`} style={{
              display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 9, color: '#64748b',
              lineHeight: 1.3, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
            }}>
              <span style={{ color: meta.color, fontWeight: 700, flexShrink: 0 }}>·</span>
              <code style={{ fontSize: 9, color: KC_MID, fontWeight: 600 }}>{key}</code>
            </div>
          ))}
          {page.sections.length > MAX_VISIBLE_SECTIONS && (
            <div style={{ fontSize: 9, color: '#94a3b8', fontStyle: 'italic' }}>
              + {page.sections.length - MAX_VISIBLE_SECTIONS} weitere
            </div>
          )}
        </div>
      )}

      <Handle type="source" position={Position.Bottom}
        style={{ background: meta.color, width: 8, height: 8, border: 'none' }}
      />
    </div>
  );
}

const NODE_TYPES = { page: PageNode };

// ── Layout (dagre) ───────────────────────────────────────────────────────────

function layoutTree(pages, blocksByPageId) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 40, ranksep: 70 });

  // Pro-Node-Höhe je nach Section-Anzahl, damit dagre die Karten kollisionsfrei
  // platziert wenn manche Karten viele Sections haben.
  const heightById = new Map();
  pages.forEach((p) => {
    const sCount = Array.isArray(p.sections) ? p.sections.length : 0;
    const h = nodeHeightForSections(sCount);
    heightById.set(p.id, h);
    g.setNode(String(p.id), { width: NODE_W, height: h });
  });
  pages.forEach((p) => {
    if (p.parent_id) g.setEdge(String(p.parent_id), String(p.id));
  });
  dagre.layout(g);

  const nodes = pages.map((p) => {
    const pos = g.node(String(p.id));
    const h = heightById.get(p.id) || NODE_H_BASE;
    return {
      id: String(p.id),
      type: 'page',
      position: { x: pos.x - NODE_W / 2, y: pos.y - h / 2 },
      data: { page: p, blockCount: (blocksByPageId.get(p.id) || []).length },
    };
  });

  const parentEdges = pages
    .filter((p) => p.parent_id)
    .map((p) => ({
      id: `e-${p.parent_id}-${p.id}`,
      source: String(p.parent_id),
      target: String(p.id),
      type: 'smoothstep',
      style: { stroke: '#94a3b8', strokeWidth: 1.5 },
    }));

  // Phase 3: "Ersetzt"-Mappings — KI-Vorschlag → konsolidierte Bestandsseiten.
  // Visuell als gestrichelte rote Edge, die auf den ersten Blick zeigt, welche
  // Bestandspages durch den KI-Vorschlag entfallen / ersetzt werden.
  const pageIdSet = new Set(pages.map((p) => p.id));
  const replaceEdges = [];
  pages.forEach((p) => {
    const ids = Array.isArray(p.replaces_page_ids) ? p.replaces_page_ids : [];
    ids.forEach((bestandId) => {
      if (!pageIdSet.has(bestandId) || bestandId === p.id) return;
      replaceEdges.push({
        id: `r-${p.id}-${bestandId}`,
        source: String(p.id),
        target: String(bestandId),
        type: 'straight',
        animated: false,
        label: 'ersetzt',
        labelStyle: { fill: '#DC2626', fontSize: 10, fontWeight: 700 },
        labelBgStyle: { fill: '#FEF2F2' },
        labelBgPadding: [4, 2],
        style: { stroke: '#DC2626', strokeWidth: 1.5, strokeDasharray: '6 4' },
      });
    });
  });

  return { nodes, edges: [...parentEdges, ...replaceEdges] };
}

// ── Main ─────────────────────────────────────────────────────────────────────

export default function SitemapView({
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
  const [importing, setImporting] = useState(false);
  // Lücke 1 (Relume-Vergleich): Side-Panel rechts beim Klick auf eine Page-Card
  const [selectedPageId, setSelectedPageId] = useState(null);
  // Lücke 2: Quick-Add-Form — null = aus, sonst { parent_id: number|null } oder 'top' für Top-Level
  const [addPageState, setAddPageState] = useState(null);
  // R1 Relume-Parität: User-gewählte Page-Anzahl beim KI-Generate (0 = Auto)
  const [pageCount, setPageCount] = useState(0);
  // R2 Relume-Parität: „+ Mehr Pages"-Dialog (Continue-generating)
  const [moreState, setMoreState] = useState(null); // null | { count: N, busy: bool }
  // R2 Feature 4: Variant-Slot — 'primary' (live) oder 'variant' (Alternative)
  const [currentVariant, setCurrentVariant] = useState('primary');
  const [variantPagesCount, setVariantPagesCount] = useState(0);

  const loadPages = useCallback(() => {
    if (!leadId) return;
    setLoading(true);
    setError('');
    // Lade aktuellen Tab + parallel Variant-Count (für Tab-Bar-Anzeige)
    Promise.all([
      fetch(`${API_BASE_URL}/api/sitemap/${leadId}?variant=${currentVariant}`, { headers })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))),
      fetch(`${API_BASE_URL}/api/sitemap/${leadId}?variant=variant`, { headers })
        .then((r) => (r.ok ? r.json() : []))
        .catch(() => []),
    ])
      .then(([data, variantData]) => {
        setPages(Array.isArray(data) ? data : data.pages || []);
        const variantList = Array.isArray(variantData) ? variantData : variantData.pages || [];
        setVariantPagesCount(variantList.length);
      })
      .catch((e) => setError(e.message || 'Sitemap konnte nicht geladen werden'))
      .finally(() => setLoading(false));
  }, [leadId, headers, currentVariant]);

  useEffect(() => { loadPages(); }, [loadPages]);

  // ── Phase 4: re-parent via edge connect, entparent via edge click ──────────

  const isAncestor = useCallback((potentialAncestorId, descendantId) => {
    // Walk up the parent chain from descendantId; return true if we hit
    // potentialAncestorId. Used to reject edges that would create a cycle.
    const byId = new Map(pages.map((p) => [p.id, p]));
    let current = byId.get(descendantId);
    let safety = pages.length + 1;
    while (current && current.parent_id && safety-- > 0) {
      if (current.parent_id === potentialAncestorId) return true;
      current = byId.get(current.parent_id);
    }
    return false;
  }, [pages]);

  const persistParentChange = useCallback(async (childId, newParentId) => {
    // Only the changed page needs to be sent — backend's /reorder is a partial
    // update keyed by id. We keep the page's existing position untouched.
    const child = pages.find((p) => p.id === childId);
    if (!child) return;
    const body = [{ id: childId, position: child.position ?? 0, parent_id: newParentId }];
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/reorder`, {
        method: 'PUT', headers, body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        const msg = typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      // Optimistic local update so the tree re-layouts without a round-trip
      setPages((prev) => prev.map((p) =>
        p.id === childId ? { ...p, parent_id: newParentId } : p,
      ));
    } catch (e) {
      toast.error(`Speichern fehlgeschlagen: ${e.message}`);
      loadPages(); // resync to server state on failure
    }
  }, [pages, leadId, headers, loadPages]);

  const handleConnect = useCallback((conn) => {
    const sourceId = parseInt(conn.source, 10);
    const targetId = parseInt(conn.target, 10);
    if (!sourceId || !targetId || sourceId === targetId) return;

    const target = pages.find((p) => p.id === targetId);
    const source = pages.find((p) => p.id === sourceId);
    if (!target || !source) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können nicht umgehängt werden.');
      return;
    }
    if (target.parent_id === sourceId) return; // no-op
    if (isAncestor(targetId, sourceId)) {
      toast.error('Verbindung erzeugt eine Schleife — abgebrochen.');
      return;
    }
    persistParentChange(targetId, sourceId);
    toast.success(`„${target.page_name}" ist jetzt Kind von „${source.page_name}"`);
  }, [pages, isAncestor, persistParentChange]);

  // ── Lücke 1: Page-Detail bearbeiten (PUT /api/sitemap/pages/:id) ───────────

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

  // ── R2 Feature 4: Variant-Slot (alternative Sitemap zum Vergleich) ────────

  const generateVariant = useCallback(async (count) => {
    if (!leadId) return;
    const t = toast.loading('KI generiert Alternative…');
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/generate`, {
        method: 'POST', headers,
        body: JSON.stringify({ as_variant: true, page_count: count || 0 }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const msg = typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      toast.success(`Alternative mit ${body.pages?.length || 0} Seiten generiert`, { id: t });
      setCurrentVariant('variant');
      // loadPages wird durch currentVariant-Effect getriggert
    } catch (e) {
      toast.error(e.message, { id: t });
    }
  }, [leadId, headers]);

  const promoteVariant = useCallback(async () => {
    if (!leadId) return;
    if (!window.confirm(
      'Variante als Hauptversion übernehmen?\n\n' +
      'Aktuelle KI-Vorschläge im Primary werden ersetzt. Bestand und manuelle Seiten bleiben.',
    )) return;
    const t = toast.loading('Variante wird übernommen…');
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/promote-variant`, {
        method: 'POST', headers,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      toast.success('Variante ist jetzt Hauptversion', { id: t });
      setCurrentVariant('primary');
    } catch (e) {
      toast.error(e.message, { id: t });
    }
  }, [leadId, headers]);

  const discardVariant = useCallback(async () => {
    if (!leadId) return;
    if (!window.confirm('Variante endgültig verwerfen?')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/discard-variant`, {
        method: 'DELETE', headers,
      });
      if (!res.ok && res.status !== 204) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      toast.success('Variante verworfen');
      setCurrentVariant('primary');
    } catch (e) {
      toast.error(e.message);
    }
  }, [leadId, headers]);

  // ── R2: Continue-generating (POST /api/sitemap/:leadId/generate-more) ──────

  const generateMore = useCallback(async (additional) => {
    if (!leadId || !additional) return;
    const t = toast.loading(`KI ergänzt ${additional} weitere Seiten…`);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/generate-more`, {
        method: 'POST', headers,
        body: JSON.stringify({ additional_pages: additional }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        throw new Error(typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`);
      }
      toast.success(`${body.added} Seite${body.added === 1 ? '' : 'n'} ergänzt`, { id: t });
      loadPages();
    } catch (e) {
      toast.error(e.message, { id: t });
    }
  }, [leadId, headers, loadPages]);

  // ── Lücke 2: Page anlegen (POST /api/sitemap/:leadId/pages) ────────────────

  const createPage = useCallback(async (parentId, name, pageType) => {
    if (!leadId || !name?.trim()) return null;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
        method: 'POST', headers,
        body: JSON.stringify({
          page_name: name.trim(),
          page_type: pageType || 'info',
          parent_id: parentId || null,
          position: pages.length,
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

  const handleEdgeClick = useCallback((_evt, edge) => {
    // Only parent edges (id prefix 'e-') are removable. Replace-mapping edges
    // (prefix 'r-') are derived from replaces_page_ids and read-only.
    if (!edge.id.startsWith('e-')) return;
    const targetId = parseInt(edge.target, 10);
    const target = pages.find((p) => p.id === targetId);
    if (!target) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können nicht umgehängt werden.');
      return;
    }
    if (!window.confirm(`Verbindung lösen — „${target.page_name}" wird zur Top-Level-Seite. Fortfahren?`)) return;
    persistParentChange(targetId, null);
  }, [pages, persistParentChange]);

  const handleImportExisting = async () => {
    if (!leadId) {
      toast.error('Lead-ID fehlt — Bestand kann nicht geladen werden.');
      return;
    }
    setImporting(true);
    const t = toast.loading('Bestand wird gecrawlt — kann 10-30 s dauern…');
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/import-existing`, {
        method: 'POST', headers,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body.detail;
        const msg = typeof detail === 'string'
          ? detail
          : detail?.message || detail?.code || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      toast.success(
        `${body.imported} Seite${body.imported === 1 ? '' : 'n'} aus Bestand importiert`,
        { id: t },
      );
      loadPages();
    } catch (e) {
      toast.error(e.message, { id: t });
    } finally {
      setImporting(false);
    }
  };

  const blocksByPageId = useMemo(() => {
    const map = new Map();
    (wireframeData?.pages || []).forEach((p) => {
      map.set(p.page_id, (p.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)));
    });
    return map;
  }, [wireframeData]);

  const totalBlocks = (wireframeData?.pages || []).reduce(
    (sum, p) => sum + (p.blocks?.length || 0),
    0,
  );

  const { nodes, edges } = useMemo(() => {
    if (pages.length === 0) return { nodes: [], edges: [] };
    const out = layoutTree(pages, blocksByPageId);
    // Lock Pflichtseiten — they cannot be reparented; UX makes that explicit.
    const locked = out.nodes.map((n) => {
      const isPflicht = !!n.data?.page?.ist_pflichtseite;
      return isPflicht
        ? { ...n, draggable: false, connectable: false }
        : n;
    });
    return { nodes: locked, edges: out.edges };
  }, [pages, blocksByPageId]);

  return (
    <div style={{
      padding: 24, fontFamily: 'var(--font-sans, system-ui)',
      height: '100%', display: 'flex', flexDirection: 'column',
    }}>
      {/* Topbar */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', gap: 12,
        alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 20, flexShrink: 0,
      }}>
        <div>
          <h1 style={{
            fontSize: 22, fontWeight: 900, color: KC_DARK, margin: 0,
            textTransform: 'uppercase', letterSpacing: '-0.02em',
          }}>
            Sitemap
          </h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            {pages.length} Seite{pages.length === 1 ? '' : 'n'} · {totalBlocks} Block-Zuweisung{totalBlocks === 1 ? '' : 'en'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {currentVariant === 'primary' && (
            <button
              type="button" onClick={handleImportExisting} disabled={importing}
              style={{
                background: 'transparent', color: KC_MID,
                border: `1.5px solid ${KC_MID}`, borderRadius: 8,
                padding: '9px 16px', fontSize: 13, fontWeight: 700,
                cursor: importing ? 'wait' : 'pointer',
                opacity: importing ? 0.6 : 1,
              }}
            >
              {importing ? 'Crawlt…' : '📥 Bestand importieren'}
            </button>
          )}
          {currentVariant === 'primary' && (
            <button
              type="button" onClick={() => setAddPageState({ parent_id: null })}
              style={{
                background: 'transparent', color: KC_MID,
                border: `1.5px solid ${KC_MID}`, borderRadius: 8,
                padding: '9px 16px', fontSize: 13, fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              + Neue Seite
            </button>
          )}
          <button
            type="button" onClick={() => setMoreState({ count: 3 })}
            disabled={pages.length === 0 || currentVariant !== 'primary'}
            style={{
              background: 'transparent', color: '#7c3aed',
              border: '1.5px solid #7c3aed', borderRadius: 8,
              padding: '9px 16px', fontSize: 13, fontWeight: 700,
              cursor: pages.length === 0 || currentVariant !== 'primary' ? 'not-allowed' : 'pointer',
              opacity: pages.length === 0 || currentVariant !== 'primary' ? 0.5 : 1,
            }}
            title={currentVariant !== 'primary'
              ? 'Nur im Primary-Tab verfügbar'
              : 'KI schlägt N weitere Seiten vor — bestehende bleiben'}
          >
            + Mehr KI-Vorschläge
          </button>
          {currentVariant === 'primary' && (
            <button
              type="button" onClick={() => generateVariant(pageCount)}
              style={{
                background: '#fff', color: KC_DARK,
                border: `1.5px dashed ${KC_DARK}`, borderRadius: 8,
                padding: '9px 16px', fontSize: 13, fontWeight: 700,
                cursor: 'pointer',
              }}
              title="Generiere parallele KI-Alternative — Primary bleibt unangetastet"
            >
              ⊕ Alternative generieren
            </button>
          )}
          {currentVariant === 'variant' && (
            <>
              <button
                type="button" onClick={promoteVariant}
                style={{
                  background: '#059669', color: '#fff',
                  border: 'none', borderRadius: 8,
                  padding: '10px 18px', fontSize: 13, fontWeight: 800,
                  cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.04em',
                }}
              >
                ✓ Variante übernehmen
              </button>
              <button
                type="button" onClick={discardVariant}
                style={{
                  background: '#fff', color: '#dc2626',
                  border: '1.5px solid #dc2626', borderRadius: 8,
                  padding: '9px 16px', fontSize: 13, fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                × Variante verwerfen
              </button>
            </>
          )}
          <select
            value={pageCount}
            onChange={(e) => setPageCount(parseInt(e.target.value, 10) || 0)}
            title="Seitenanzahl beim KI-Vorschlag"
            style={{
              padding: '9px 10px',
              border: '1.5px solid #cbd5e1', borderRadius: 8,
              background: '#fff', color: '#475569',
              fontSize: 12, cursor: 'pointer',
              fontFamily: 'var(--font-sans, system-ui)',
            }}
          >
            {PAGE_COUNT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={async () => {
              if (currentVariant === 'variant') {
                await generateVariant(pageCount);
              } else {
                await onRegenerateSitemap?.(pageCount);
                // Parent feuert nur den POST und schlucks Errors. Wir laden
                // die Tree-View nach 1.5 s neu, damit der Vorschlag sichtbar wird.
                setTimeout(loadPages, 1500);
              }
            }}
            style={{
              background: 'transparent', color: KC_DARK,
              border: `1.5px solid ${KC_DARK}`, borderRadius: 8,
              padding: '9px 16px', fontSize: 13, fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            {currentVariant === 'variant' ? '↻ Variante neu generieren' : 'Sitemap neu generieren'}
          </button>
          {currentVariant === 'primary' && (
            <button
              type="button" onClick={onGenerateWireframe} disabled={pages.length === 0}
              style={{
                background: KC_YELLOW, color: '#000',
                border: 'none', borderRadius: 8,
                padding: '10px 18px', fontSize: 13, fontWeight: 800,
                cursor: pages.length === 0 ? 'not-allowed' : 'pointer',
                opacity: pages.length === 0 ? 0.5 : 1,
                textTransform: 'uppercase', letterSpacing: '0.04em',
              }}
            >
              KI-Wireframe erzeugen
            </button>
          )}
          {currentVariant === 'primary' && (
            <button
              type="button" onClick={onNavigateToWireframe} disabled={totalBlocks === 0}
              style={{
                background: KC_MID, color: '#fff',
                border: 'none', borderRadius: 8,
                padding: '10px 18px', fontSize: 13, fontWeight: 700,
                cursor: totalBlocks === 0 ? 'not-allowed' : 'pointer',
                opacity: totalBlocks === 0 ? 0.5 : 1,
              }}
            >
              Zu Wireframe →
            </button>
          )}
        </div>
      </div>

      {/* R2 Feature 4: Variant-Tabs — sichtbar nur wenn eine Alternative existiert */}
      {variantPagesCount > 0 && (
        <div style={{
          display: 'flex', gap: 0, marginBottom: 16, flexShrink: 0,
          borderBottom: '1px solid #e2e8f0',
        }}>
          {[
            { id: 'primary', label: 'Primary (live)' },
            { id: 'variant', label: `Alternative (${variantPagesCount})` },
          ].map((tab) => {
            const isActive = currentVariant === tab.id;
            return (
              <button
                key={tab.id} type="button"
                onClick={() => setCurrentVariant(tab.id)}
                style={{
                  padding: '8px 18px',
                  background: 'transparent', border: 'none',
                  borderBottom: isActive ? `2px solid ${KC_MID}` : '2px solid transparent',
                  color: isActive ? KC_DARK : '#64748b',
                  fontSize: 13, fontWeight: isActive ? 800 : 500,
                  cursor: 'pointer', fontFamily: 'inherit',
                  marginBottom: -1,
                }}
              >
                {tab.label}
              </button>
            );
          })}
          <div style={{ flex: 1 }} />
          {currentVariant === 'variant' && (
            <span style={{ alignSelf: 'center', fontSize: 11, color: '#94a3b8', padding: '0 8px' }}>
              Pflichtseiten + Bestand werden bei Übernahme aus Primary mitgenommen
            </span>
          )}
        </div>
      )}

      {loading && <div style={{ color: '#64748b', fontSize: 14 }}>Sitemap wird geladen…</div>}
      {error && (
        <div style={{ background: '#FEF2F2', color: '#991B1B', padding: 12, borderRadius: 8, fontSize: 13 }}>
          {error}
        </div>
      )}

      {!loading && !error && pages.length === 0 && (
        <div style={{
          border: '2px dashed #cbd5e1', borderRadius: 16, padding: 40,
          textAlign: 'center', color: '#64748b',
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🗺</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: KC_DARK, marginBottom: 6 }}>
            Noch keine Sitemap-Seiten
          </div>
          <div style={{ fontSize: 13, marginBottom: 16 }}>
            Importiere die Bestands-Website oder lass die KI eine neue Struktur vorschlagen.
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button" onClick={handleImportExisting} disabled={importing}
              style={{
                background: KC_MID, color: '#fff',
                border: 'none', borderRadius: 8,
                padding: '10px 18px', fontSize: 13, fontWeight: 700,
                cursor: importing ? 'wait' : 'pointer',
              }}
            >
              {importing ? 'Crawlt…' : '📥 Bestand importieren'}
            </button>
            <button
              type="button" onClick={onRegenerateSitemap}
              style={{
                background: KC_YELLOW, color: '#000',
                border: 'none', borderRadius: 8,
                padding: '10px 18px', fontSize: 13, fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              KI-Vorschlag generieren
            </button>
          </div>
        </div>
      )}

      {!loading && !error && pages.length > 0 && (
        <div style={{ flex: 1, minHeight: 500, display: 'flex', gap: 12 }}>
          <div style={{
            flex: 1, minWidth: 0,
            background: '#f8fafc', borderRadius: 12,
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
          }}>
            <ReactFlowProvider>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={NODE_TYPES}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.2}
                maxZoom={1.5}
                nodesDraggable
                nodesConnectable
                elementsSelectable
                onConnect={handleConnect}
                onEdgeClick={handleEdgeClick}
                onNodeClick={(_e, node) => {
                  const pageId = parseInt(node.id, 10);
                  if (pageId) setSelectedPageId(pageId);
                }}
                defaultEdgeOptions={{ type: 'smoothstep' }}
              >
                <Background gap={16} color="#e2e8f0" />
                <Controls showInteractive={false} />
                <Panel position="top-left" style={{
                  background: 'rgba(255,255,255,0.92)', border: '1px solid #e2e8f0',
                  borderRadius: 8, padding: '6px 10px', fontSize: 11, color: '#475569',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                }}>
                  💡 Karte klicken = Details rechts · Kartenrand ziehen = neue Hierarchie · Linie klicken = entkoppeln
                </Panel>
                <MiniMap
                  pannable zoomable
                  nodeColor={(n) => {
                    const meta = TYPE_META[n.data?.page?.page_type] || TYPE_META.info;
                    return meta.color;
                  }}
                />
              </ReactFlow>
            </ReactFlowProvider>
          </div>

          {/* Lücke 1: Side-Panel — Page-Details + Section-Editor */}
          {selectedPageId && (
            <PageDetailPanel
              page={pages.find((p) => p.id === selectedPageId) || null}
              onClose={() => setSelectedPageId(null)}
              onSave={(updates) => savePageDetails(selectedPageId, updates)}
              onAddChild={() => setAddPageState({ parent_id: selectedPageId })}
            />
          )}
        </div>
      )}

      {/* Lücke 2: Add-Page-Dialog (top-level oder als Sub-Page) */}
      {addPageState && (
        <AddPageDialog
          parentId={addPageState.parent_id}
          parentName={addPageState.parent_id
            ? (pages.find((p) => p.id === addPageState.parent_id)?.page_name || '')
            : null}
          onClose={() => setAddPageState(null)}
          onSubmit={async (name, type) => {
            const created = await createPage(addPageState.parent_id, name, type);
            if (created) setAddPageState(null);
          }}
        />
      )}

      {/* R2: Continue-generating dialog */}
      {moreState && (
        <MorePagesDialog
          initial={moreState.count}
          onClose={() => setMoreState(null)}
          onSubmit={async (count) => {
            setMoreState({ count, busy: true });
            await generateMore(count);
            setMoreState(null);
          }}
        />
      )}
    </div>
  );
}

// ── R2: Continue-generating Dialog ────────────────────────────────────────────

function MorePagesDialog({ initial, onClose, onSubmit }) {
  const [count, setCount] = useState(initial || 3);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (busy || count < 1) return;
    setBusy(true);
    await onSubmit(count);
    setBusy(false);
  };

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <form onSubmit={handleSubmit} style={{
        background: '#fff', borderRadius: 12, padding: 20,
        width: '100%', maxWidth: 380, boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <h3 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 700, color: KC_DARK }}>
          Mehr KI-Vorschläge generieren
        </h3>
        <p style={{ margin: '0 0 16px', fontSize: 11, color: '#64748b' }}>
          Bestehende Seiten bleiben unverändert. Die KI schlägt nur zusätzliche Inhaltsseiten vor.
        </p>
        <div style={{ marginBottom: 16 }}>
          <label style={lblStyle}>Anzahl</label>
          <select value={count} onChange={(e) => setCount(parseInt(e.target.value, 10) || 3)}
            style={{ ...inpStyle(false), cursor: 'pointer' }}>
            {[1, 2, 3, 4, 5, 6, 8, 10].map((n) => (
              <option key={n} value={n}>{n} {n === 1 ? 'Seite' : 'Seiten'}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose} disabled={busy}
            style={{ padding: '8px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, cursor: 'pointer', color: '#64748b' }}>
            Abbrechen
          </button>
          <button type="submit" disabled={busy}
            style={{
              padding: '8px 18px',
              background: busy ? '#94a3b8' : '#7c3aed',
              color: '#fff', border: 'none', borderRadius: 8,
              fontSize: 12, fontWeight: 700,
              cursor: busy ? 'wait' : 'pointer',
            }}>
            {busy ? 'KI läuft…' : '+ Generieren'}
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Lücke 1: Side-Panel mit Section-Editor ────────────────────────────────────

function PageDetailPanel({ page, onClose, onSave, onAddChild }) {
  // Lokaler Form-State, damit User mehrere Felder ändern und mit einem Save
  // committen kann. Beim Wechsel der Seite (page.id ändert) wird neu gefüllt.
  const [form, setForm] = useState(() => ({
    page_name: page?.page_name || '',
    page_type: page?.page_type || 'info',
    status:    page?.status    || 'geplant',
    sections:  Array.isArray(page?.sections) ? [...page.sections] : [],
    ai_prompt: page?.ai_prompt || '',
    color_tag: page?.color_tag || '',
  }));
  const [saving, setSaving] = useState(false);
  const [addingSection, setAddingSection] = useState(false);
  // R2 Feature 6: Search-Filter für den Section-Catalog beim Hinzufügen
  const [sectionSearch, setSectionSearch] = useState('');

  useEffect(() => {
    setForm({
      page_name: page?.page_name || '',
      page_type: page?.page_type || 'info',
      status:    page?.status    || 'geplant',
      sections:  Array.isArray(page?.sections) ? [...page.sections] : [],
      ai_prompt: page?.ai_prompt || '',
      color_tag: page?.color_tag || '',
    });
  }, [page?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!page) return null;
  const isPflicht = !!page.ist_pflichtseite;

  const moveSection = (idx, dir) => {
    const next = [...form.sections];
    const target = idx + dir;
    if (target < 0 || target >= next.length) return;
    [next[idx], next[target]] = [next[target], next[idx]];
    setForm((f) => ({ ...f, sections: next }));
  };
  const removeSection = (idx) => {
    setForm((f) => ({ ...f, sections: f.sections.filter((_, i) => i !== idx) }));
  };
  const addSection = (key) => {
    if (!key || !SECTION_CATALOG[key]) return;
    setForm((f) => ({ ...f, sections: [...f.sections, key] }));
    setAddingSection(false);
    setSectionSearch('');
  };

  const handleSave = async () => {
    setSaving(true);
    await onSave(form);
    setSaving(false);
  };

  const meta = TYPE_META[form.page_type] || TYPE_META.info;
  const availableSections = Object.keys(SECTION_CATALOG); // alle verfügbar — User kann auch Duplikate setzen wenn er will

  return (
    <aside style={{
      width: 360, flexShrink: 0,
      background: '#fff', borderRadius: 12,
      border: '1px solid #e2e8f0',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 14px', borderBottom: '1px solid #e2e8f0',
        background: meta.color + '0d',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <span style={{ fontSize: 18 }}>{meta.icon}</span>
          <div style={{ fontSize: 13, fontWeight: 700, color: KC_DARK, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {form.page_name || 'Seite'}
          </div>
        </div>
        <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 16, cursor: 'pointer', color: '#64748b', padding: 0 }} aria-label="Schließen">×</button>
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {isPflicht && (
          <div style={{ fontSize: 11, color: '#92400E', background: '#FEF3C7', padding: '6px 8px', borderRadius: 6 }}>
            🔒 Pflichtseite — nur Status / Notizen / Sections änderbar
          </div>
        )}

        <div>
          <label style={lblStyle}>Page-Name</label>
          <input
            type="text" value={form.page_name} disabled={isPflicht}
            onChange={(e) => setForm((f) => ({ ...f, page_name: e.target.value }))}
            style={inpStyle(isPflicht)}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={lblStyle}>Type</label>
            <select
              value={form.page_type} disabled={isPflicht}
              onChange={(e) => setForm((f) => ({ ...f, page_type: e.target.value }))}
              style={{ ...inpStyle(isPflicht), cursor: isPflicht ? 'not-allowed' : 'pointer' }}
            >
              {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label style={lblStyle}>Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              style={{ ...inpStyle(false), cursor: 'pointer' }}
            >
              {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label style={lblStyle}>Color-Tag</label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {COLOR_TAG_PRESETS.map((c) => {
              const isSelected = form.color_tag === c.value;
              return (
                <button
                  key={c.value || 'none'} type="button"
                  onClick={() => setForm((f) => ({ ...f, color_tag: c.value }))}
                  title={c.label}
                  style={{
                    width: 24, height: 24, borderRadius: 6,
                    background: c.value || 'transparent',
                    border: c.value ? '1px solid rgba(0,0,0,0.1)' : '1px dashed #cbd5e1',
                    boxShadow: isSelected ? `0 0 0 2px ${KC_MID}` : 'none',
                    cursor: 'pointer', padding: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#94a3b8', fontSize: 11,
                  }}
                >
                  {!c.value ? '×' : ''}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label style={lblStyle}>Goal / KI-Anweisung (optional)</label>
          <textarea
            value={form.ai_prompt}
            onChange={(e) => setForm((f) => ({ ...f, ai_prompt: e.target.value }))}
            placeholder="z.B. „Lead-Capture für Wallbox-Interessenten — Fokus auf Förderung 2026"
            rows={3}
            style={{ ...inpStyle(false), resize: 'vertical', fontFamily: 'inherit', minHeight: 60 }}
          />
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>
            Wird beim KI-Content-Generator als Per-Page-Kontext mitgegeben.
          </div>
        </div>

        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
            <label style={lblStyle}>Sections ({form.sections.length})</label>
            <button
              type="button"
              onClick={() => { setAddingSection((v) => !v); setSectionSearch(''); }}
              style={{
                background: 'none', border: 'none', color: KC_MID,
                fontSize: 11, fontWeight: 700, cursor: 'pointer', padding: 0,
              }}
            >
              {addingSection ? '× Schließen' : '+ Section'}
            </button>
          </div>

          {addingSection && (
            <div style={{ marginBottom: 10, padding: 8, background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
              <input
                type="search" placeholder="Suchen (Name oder Beschreibung)…"
                value={sectionSearch}
                onChange={(e) => setSectionSearch(e.target.value)}
                autoFocus
                style={{ ...inpStyle(false), marginBottom: 6 }}
              />
              <div style={{ maxHeight: 220, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 3 }}>
                {availableSections
                  .filter((key) => {
                    const q = sectionSearch.trim().toLowerCase();
                    if (!q) return true;
                    const desc = SECTION_CATALOG[key].toLowerCase();
                    return key.toLowerCase().includes(q) || desc.includes(q);
                  })
                  .map((key) => (
                    <button
                      key={key} type="button"
                      onClick={() => addSection(key)}
                      style={{
                        display: 'flex', alignItems: 'flex-start', gap: 8,
                        padding: '6px 8px',
                        background: '#fff', border: '1px solid #e2e8f0', borderRadius: 4,
                        cursor: 'pointer', textAlign: 'left', fontSize: 11,
                        fontFamily: 'inherit', color: 'inherit',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = '#eff6ff'; e.currentTarget.style.borderColor = KC_MID; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.borderColor = '#e2e8f0'; }}
                    >
                      <code style={{ color: KC_MID, fontWeight: 700, minWidth: 110, flexShrink: 0 }}>{key}</code>
                      <span style={{ color: '#475569', flex: 1, lineHeight: 1.35 }}>{SECTION_CATALOG[key]}</span>
                    </button>
                  ))}
                {availableSections.filter((key) => {
                  const q = sectionSearch.trim().toLowerCase();
                  if (!q) return true;
                  return key.toLowerCase().includes(q) || SECTION_CATALOG[key].toLowerCase().includes(q);
                }).length === 0 && (
                  <div style={{ fontSize: 11, color: '#94a3b8', fontStyle: 'italic', padding: '8px 4px' }}>
                    Keine Section passt zu „{sectionSearch}".
                  </div>
                )}
              </div>
            </div>
          )}

          {form.sections.length === 0 ? (
            <div style={{ fontSize: 11, color: '#94a3b8', fontStyle: 'italic', padding: '6px 0' }}>
              Keine Sections — KI-Vorschläge oder manuell ergänzen.
            </div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
              {form.sections.map((key, idx) => (
                <li key={`${key}-${idx}`} style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 8px', background: '#f8fafc',
                  border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 11,
                }}>
                  <span style={{ color: '#64748b', fontVariantNumeric: 'tabular-nums', minWidth: 16 }}>{idx + 1}.</span>
                  <code style={{ fontSize: 11, color: KC_MID, fontWeight: 700, flexShrink: 0 }}>{key}</code>
                  <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#475569' }}>
                    {SECTION_CATALOG[key] || '—'}
                  </span>
                  <button type="button" onClick={() => moveSection(idx, -1)} disabled={idx === 0} title="Nach oben"
                    style={{ background: 'none', border: 'none', cursor: idx === 0 ? 'default' : 'pointer', color: idx === 0 ? '#cbd5e1' : '#64748b', padding: '0 2px', fontSize: 11 }}>↑</button>
                  <button type="button" onClick={() => moveSection(idx, 1)} disabled={idx === form.sections.length - 1} title="Nach unten"
                    style={{ background: 'none', border: 'none', cursor: idx === form.sections.length - 1 ? 'default' : 'pointer', color: idx === form.sections.length - 1 ? '#cbd5e1' : '#64748b', padding: '0 2px', fontSize: 11 }}>↓</button>
                  <button type="button" onClick={() => removeSection(idx)} title="Section entfernen"
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', padding: '0 2px', fontSize: 12 }}>×</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: 12 }}>
          <button
            type="button" onClick={onAddChild}
            style={{
              width: '100%', padding: '8px 12px',
              background: 'transparent', color: KC_MID,
              border: `1.5px dashed ${KC_MID}`, borderRadius: 8,
              fontSize: 12, fontWeight: 700, cursor: 'pointer',
            }}
          >
            + Sub-Seite unter „{form.page_name || 'dieser Seite'}"
          </button>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '10px 14px', borderTop: '1px solid #e2e8f0',
        display: 'flex', gap: 8, background: '#f8fafc',
      }}>
        <button type="button" onClick={onClose}
          style={{ flex: 1, padding: '8px 12px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, cursor: 'pointer', color: '#64748b' }}>
          Abbrechen
        </button>
        <button type="button" onClick={handleSave} disabled={saving}
          style={{ flex: 1, padding: '8px 12px', background: saving ? '#94a3b8' : KC_MID, color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: saving ? 'wait' : 'pointer' }}>
          {saving ? 'Speichert…' : '✓ Speichern'}
        </button>
      </div>
    </aside>
  );
}

// ── Lücke 2: Add-Page-Dialog (kleines Modal) ──────────────────────────────────

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
        width: '100%', maxWidth: 420,
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
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
          <input
            type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="z.B. Wallbox-Installation"
            style={inpStyle(false)} autoFocus
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={lblStyle}>Page-Type</label>
          <select value={pageType} onChange={(e) => setPageType(e.target.value)} style={{ ...inpStyle(false), cursor: 'pointer' }}>
            {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, cursor: 'pointer', color: '#64748b' }}>
            Abbrechen
          </button>
          <button type="submit" disabled={!name.trim() || busy}
            style={{
              padding: '8px 18px',
              background: !name.trim() || busy ? '#94a3b8' : KC_MID,
              color: '#fff', border: 'none', borderRadius: 8,
              fontSize: 12, fontWeight: 700,
              cursor: !name.trim() || busy ? 'not-allowed' : 'pointer',
            }}
          >
            {busy ? 'Anlegen…' : '+ Anlegen'}
          </button>
        </div>
      </form>
    </div>
  );
}

const lblStyle = {
  display: 'block', fontSize: 10, fontWeight: 700, color: '#64748b',
  textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4,
};
const inpStyle = (disabled) => ({
  width: '100%', boxSizing: 'border-box', padding: '7px 10px',
  border: '1px solid #e2e8f0', borderRadius: 6,
  background: disabled ? '#f8fafc' : '#fff',
  color: disabled ? '#94a3b8' : '#1A2C32',
  fontSize: 12, fontFamily: 'inherit', outline: 'none',
});
